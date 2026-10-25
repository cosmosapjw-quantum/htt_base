# Conditional covariance sets for a seven-channel tensor response

Prepared 2026-10-24. Owner of this note: independent theory/source reviewer. Requested runtime `gpt-6-astra/xhigh`; observed runtime `UNKNOWN`. Status: **DERIVED under explicit finite-dimensional assumptions; independent proof review and finite checks pending**. This is a non-claim-bearing theoretical preparation, not an acknowledged controller packet, a scientific admission, a new mathematical-priority claim, or a four-axis CAS result. No actual M7 matrix was supplied or evaluated.

The consuming decision is whether a future qualified CF4 response can support a finite covariance statement and which tensor contrasts it protects. Original H02 cannot acquire finite **physical** uncertainty from an operator alone: it still needs a source-qualified bounded calibration/joint-covariance class, mean/bias and PV controls, and the physical response/domain. All existing completion counters, historical 48-task accounting, R9 UNKNOWN, and Gamma/PV/physical-functional HOLD states are untouched.

## Evidence and distinct scope

The controlling response specification is `/mnt/extdrive/workdir/htt_open_data/r26_cf4_actual_source_model_review/CONTRACT.md`, SHA-256 `cdf94aaf6d39a01baae0d2fc03342032b1eb5f82ef34555e83ca8631d43f7992`. It requires an actual full-cohort seven-channel response after held-out reconstruction succeeds. It does not provide one. Its nominal and witness representatives are conditional and do not exhaust all producer maps or supply a bound between them.

The first report's `07_mathematical_details.tex` already derives the sharp sum-of-standard-deviations covariance bound, its scalar extremizer, and the warning that different projections may require different extremizers. Its framework and P1 sections 02, 05, 07 already establish tensor-first information, fibres, coupled pushforwards, support bounds, missing/domain strata, and the difference between confidence coverage and a probability law. Those are reused here, not claimed as additions.

The distinct proposed consumer is **the exact image of a calibration covariance cone, its protected output subspace, the seven-channel gauge correction, and support functions for explicitly bounded covariance classes**. These are standard linear-algebra consequences specialized to the source-qualified branch structure. Primary methodological references and exact prior-report locations are in `CITATIONS.md`.

## 1. Domain, units, and fixed estimator

All vectors and matrices are real, finite dimensional; covariance means finite second central moment. `S_+^k` is the cone of symmetric PSD k-by-k matrices; `range`, `ker`, and Moore-Penrose inverse refer to exact algebra unless explicitly marked numerical. The coefficient vector b has d components; CF4's intended d is five in its saved Frobenius-orthonormal STF basis. Channel perturbations eta have k components in magnitudes; the intended k is seven. Thus M is d-by-k, b and eta are in mag, and M Gamma M^T is in mag^2. Bounds on trace(Gamma) apply in this fixed channel parametrization; they are not invariant under arbitrary rescaling of channels.

Write the fixed estimator as b_hat = L y, with

    L = F_E1^(-1) Bw^T P D^(-1/2),
    F_E1 = Bw^T P Bw,  P = I - Q_N Q_N^T,
    Bw = D^(-1/2) B,  Nw = D^(-1/2) N.

Assume D is positive definite, Q_N has orthonormal columns spanning range(Nw), and F_E1 is invertible. `F_E1` is the saved estimator normal matrix, not the departure filling fraction F. Changing a candidate covariance below does not refit L. The working diagonal D is not asserted to equal the actual measurement covariance. If these estimator assumptions fail, this application is undefined; replacing an inverse or nuisance space changes the contracted estimator and requires its own decision.

Set M = L A7. The mathematical results below apply to any fixed M, including rank zero, without needing a producer interpretation. Physical use additionally requires the qualified source/row/frame/operator identity specified by the response contract. Unknown mean errors are separate: covariance bounds on centered fluctuations do not bound calibration bias M E[eta], total mean squared error, or the physical parameter.

## 2. Exact covariance cone and protected contrasts

**Proposition 1.** For every M in R^(d by k),

    C(M) := {M Gamma M^T : Gamma in S_+^k}
          = {C in S_+^d : range(C) is contained in range(M)}.

**Proof.** Forward inclusion follows from quadratic-form positivity and range(M Gamma M^T) contained in range(M). Conversely, let C be PSD with its range in range(M). Set R = M M^dagger, the orthogonal projector onto range(M), and Gamma_0 = M^dagger C (M^dagger)^T. Congruence preserves PSD. Since RC = C and C is symmetric, CR = C, so M Gamma_0 M^T = R C R = C. This also covers M = 0, where both sets contain only zero. Every such Gamma_0 is a legitimate covariance of some centered finite-dimensional random vector, for example by a square-root image of a standard normal. This existence argument does not select a physical law. QED.

An equivalent test is ker(M^T) contained in ker(C). The cone is closed here because this particular image has the displayed PSD/range characterization; arbitrary linear images of closed cones need not be closed.

**Corollaries.**

1. If rank(M) = d, then C(M) = S_+^d. An arbitrary unknown PSD calibration covariance can then reproduce every output covariance shape. This is a statement about calibration covariance compatibility in the specified linear model, not identification of a physical signal or its mean.
2. A fixed linear contrast u^T b is unaffected by every channel perturbation if and only if M^T u = 0. The protected subspace has dimension d - rank(M). Necessity follows by choosing eta = M^T u; equivalently choose Gamma = (M^T u)(M^T u)^T to witness nonzero variance when M^T u is nonzero.
3. With no upper restriction on Gamma, the directional calibration-variance supremum is zero when M^T u = 0 and +infinity otherwise. For v = M^T u != 0, Gamma_t = t vv^T / ||v||^2 gives variance t ||v||^2 as t increases. Full row rank therefore leaves no nonzero protected output contrast. Rank-deficient M still has unbounded variance in every unprotected direction.
4. If eta can also have arbitrary deterministic mean, its mean displacement fills range(M). This is a separate mean-identification issue; it is not a consequence of prescribing a covariance law.

There is no diagonal-covariance restriction. For example M = [1,1] and Gamma = [[1,rho],[rho,1]], |rho| <= 1, give output variance 2 + 2 rho, ranging from 0 to 4. Deleting the off-diagonal term gives 2 and changes the question.

## 3. Seven-channel gauge versus a six-channel submatrix

**Proposition 2.** Suppose every A7 row sums to one and the constant vector 1_n belongs to range(N). Then

    A7 1_7 = 1_n,  L 1_n = 0,  M7 1_7 = 0.

Indeed D^(-1/2) 1_n lies in range(Nw), so P annihilates it. If M7 = [M6, m_cal], the exact identity is

    M6 1_6 = -m_cal,

which is zero only if the direct-calibrator response column itself is zero. No general six-channel gauge follows after removing that column. In the specified source branches, noncalibrator rows have their six normalized weights followed by zero; direct-calibrator rows have six zeros followed by one. Both branches are needed for A7 1_7 = 1_n. The two direct calibrators' separate residual errors remain in the measurement/PV joint law; a common eta_cal does not collapse them to one random error.

**Counterexample to both false inferences.** Let A7 = I_7 and L = M7 = [I_5, 0_5, -1_5]. Then L 1_7 = 0 and M7 has rank five, while M6 1_6 = 1_5 != 0. Thus a common channel gauge is compatible with a full output covariance cone and with no protected tensor contrast. This is an exact algebraic fixture, not a CF4 measurement.

The gauge is a right-null vector in channel space. Protected contrasts are left-null vectors in output space. For an orthonormal E spanning 1_7^perp, M7 = M7 E E^T and only E^T Gamma7 E enters M7 Gamma7 M7^T. Arbitrary PSD Gamma7 induces arbitrary PSD contrast covariance on that six-dimensional subspace, so removing one common mode does not create an amplitude bound. Even the full-row-rank example can realize every output C using Gamma_0 supported on 1_7^perp.

## 4. Support functions of bounded covariance classes

**Proposition 2a (whole matrix image under a trace cap).** For tau >= 0,

    {M Gamma M^T : Gamma >= 0, tr(Gamma) <= tau^2}
      = {C >= 0 : range(C) subset range(M),
                    tr(M^dagger C (M^dagger)^T) <= tau^2}.

For any PSD lift Gamma of C, let P_M = M^dagger M. Its row-space block is fixed:

    P_M Gamma P_M = M^dagger C (M^dagger)^T = Gamma_0.
    tr(Gamma) = tr(Gamma_0)
               + tr((I-P_M) Gamma (I-P_M)) >= tr(Gamma_0).

The off-diagonal blocks have zero trace. Proposition 1 constructs the feasible Gamma_0 attaining this minimum, proving both inclusions. PSD plus zero trace of the null-space block forces that block and its cross blocks to vanish, so Gamma_0 is also the unique minimum-trace PSD lift. This is a whole joint covariance set, not the product of directional intervals. The range test cannot be omitted: M=diag(1,0), C=diag(0,1) gives a zero pseudoinverse-trace cost but has no lift.

**Proposition 2b (whole matrix image under a Loewner cap).** For G >= 0,

    {M Gamma M^T : 0 <= Gamma <= G}
      = {C : 0 <= C <= M G M^T}.

One inclusion is congruence monotonicity. For the reverse, set N=M G^(1/2). If 0<=C<=NN^T, then range(C) subset range(N). Put Z=N^dagger C (N^dagger)^T; congruence gives 0<=Z<=N^dagger NN^T (N^dagger)^T=P_row(N)<=I. Thus Gamma=G^(1/2) Z G^(1/2) is feasible and N Z N^T=C. This includes singular G and M. The spectral-cap case is G=tau^2 I. It explains precisely why the trace-class directional envelope may be an attainable matrix for a larger class but not for the trace class itself.

For a stated nonempty covariance class K, let C_K(M) = {M Gamma M^T : Gamma in K}. For symmetric test matrix H define the support function with the trace inner product:

    h_C(H) = sup_{Gamma in K} tr(H M Gamma M^T)
           = h_K(M^T H M).

This identity is just cyclicity of trace and preserves all correlations. Put K_H = M^T H M and v = M^T u. For tau >= 0 and fixed PSD G:

| Explicit class K | General support h_C(H) | Directional upper variance h_C(uu^T) |
|---|---|---|
| Gamma PSD, no cap | 0 if K_H is negative semidefinite; +infinity otherwise | 0 if v=0; +infinity otherwise |
| Gamma PSD, tr(Gamma) <= tau^2 | tau^2 max(lambda_max(K_H),0) | tau^2 ||v||^2 |
| 0 <= Gamma <= tau^2 I | tau^2 tr((K_H)_+) | tau^2 ||v||^2 |
| 0 <= Gamma <= G | tr((G^(1/2) K_H G^(1/2))_+) | v^T G v |

Here X_+ keeps the positive eigenvalues of a symmetric X. A zero cap gives zero. For the trace class, diagonalize K_H and use tr(K_H Gamma) <= lambda_max(K_H) tr(Gamma) if the largest eigenvalue is positive; a rank-one covariance on a maximizing eigenvector attains it. If all eigenvalues are nonpositive, Gamma = 0 attains zero. In particular, for v != 0 the directional maximizer is Gamma = tau^2 vv^T / ||v||^2. This proves sharpness.

For the spectral/Loewner class, write Gamma = G^(1/2) Z G^(1/2) with 0 <= Z <= I. This representation also holds for singular G: Gamma <= G forces its null space to include ker(G), and the inverse square root on range(G) constructs Z; extend by zero on ker(G). In the eigenbasis of G^(1/2) K_H G^(1/2), choose Z as the projector onto positive eigenvalues. This gives the support formula. Taking G = tau^2 I gives the spectral case. The unbounded-cone row follows by scaling a positive eigenvector or, for K_H <= 0, by nonpositivity and Gamma = 0.

Consequently,

    sup_{tr(Gamma)<=tau^2} tr(M Gamma M^T) = tau^2 ||M||_op^2,
    sup_{0<=Gamma<=tau^2 I} tr(M Gamma M^T) = tau^2 ||M||_F^2.

For the trace class, C <= tau^2 M M^T is a valid common Loewner bound, but this matrix need not be attainable within that class. With M = I_2 and tau > 0, attaining the directional maximum in both e1 and e2 would require tr(Gamma) >= 2 tau^2. By contrast, the Loewner class Gamma <= G has the feasible matrix Gamma = G attaining all directional upper variances simultaneously. Matching pointwise bounds do not make the trace and spectral classes equivalent.

These formulas are parameterized sensitivity statements. Choosing tau or G needs a source or an explicitly labeled scenario; the response does not estimate them. A trace cap fixes central second moments, not bounded support of eta or a bias bound.

## 5. Full measurement/calibration/velocity covariance

Let xi = (epsilon, eta, v) have centered finite-second-moment fluctuations. Epsilon is the residual measurement/selection vector, eta the seven calibration channels, and v a declared velocity vector. If a qualified velocity-to-data response J exists, write R_v = L J; otherwise R_v is a symbolic missing response. With T = [L, M, R_v],

    delta b = T xi,
    Omega = [ C_e       K_e_eta     K_e_v  ]
            [ K_e_eta^T Gamma       K_eta_v]
            [ K_e_v^T   K_eta_v^T   C_v    ] >= 0,
    C_b = T Omega T^T.

Expanding gives the three marginal terms L C_e L^T + M Gamma M^T + R_v C_v R_v^T and all six cross terms:

    L K_e_eta M^T + M K_e_eta^T L^T,
    L K_e_v R_v^T + R_v K_e_v^T L^T,
    M K_eta_v R_v^T + R_v K_eta_v^T M^T.

If v uses km/s, J has units mag/(km/s), the cross blocks have the corresponding mixed units, and every term in C_b has units mag^2. The blocks are disjoint latent contributions only when the source decomposition says so; a released total covariance cannot be added again as an independent measurement term. Pairwise-valid correlations alone do not establish full Omega PSD. For example the scalar 3-by-3 matrix with unit diagonal and every off-diagonal entry -3/4 has PSD 2-by-2 principal blocks but eigenvalue -1/2 in direction (1,1,1).

**Proposition 3 (known marginal covariances).** Take fixed marginal matrices C_i >= 0 and fixed maps T_i for i=1,...,m; allow every jointly PSD covariance with those diagonal blocks and no further cross-block restrictions. For a fixed u put a_i = T_i^T u and s_i = sqrt(a_i^T C_i a_i). Then

    sup_Omega Var(u^T sum_i T_i X_i) = (sum_i s_i)^2.

This is the existing report's sharp scalar bound, reproduced with its full-domain assumptions. Covariance Cauchy-Schwarz proves the upper bound. For each s_i>0 put g_i = C_i a_i/s_i and choose

    X_i = g_i Z + Y_i,
    Var(Z)=1,  Cov(Y_i)=C_i-g_i g_i^T,

with Z and all Y_i mutually independent. The residual covariance is PSD by Cauchy-Schwarz in the C_i seminorm. Also a_i^T g_i=s_i and Var(a_i^T Y_i)=0, so a_i^T X_i=s_i Z almost surely. For s_i=0, C_i a_i=0 and an independent X_i with covariance C_i has zero projection. This constructs a jointly PSD Omega with exactly the full prescribed marginal covariances and attains the bound. Gaussian construction is an existence witness, not an imposed observational distribution. Fixed full marginal distributions or extra cross-block constraints may remove this extremizer.

The corresponding sharp lower value is

    inf_Omega Var(u^T sum_i T_i X_i)
      = max(2 max_i s_i - sum_i s_i, 0)^2.

The reverse triangle inequality in L2 proves the lower bound. To attain it, choose unit plane vectors e_i with weighted resultant sum_i s_i e_i of the minimal possible length: place all smaller segments opposite the longest if it dominates; otherwise close a polygon. Existence follows inductively: adding a segment of length s to a resultant of length r allows every length in [|r-s|,r+s] by varying its angle. Taking the union over the previous attainable interval yields [max(2 max_i s_i-sum_i s_i,0),sum_i s_i]. Take Z_i=e_i^T Z for a shared standard two-dimensional Z, and use X_i=g_i Z_i+Y_i with the same independent residuals as above. All marginal covariances remain C_i. Zero s_i and the all-zero case require no division. These extrema apply to each fixed direction separately.

**No simultaneous extremizer in general.** With two vector contributions having covariances diag(1,0) and diag(0,1), their sum has covariance [[1,rho],[rho,1]], |rho|<=1. The maximum in direction (1,1) requires rho=1, whereas that in direction (1,-1) requires rho=-1. The pointwise envelope (|u1|+|u2|)^2 is not one quadratic form. A valid coarse common matrix bound is C_b <= m sum_i T_i C_i T_i^T, from (sum s_i)^2 <= m sum s_i^2; it should be labeled conservative.

If nonempty marginal classes K_i are independent choices, let q_i(u)=sup_{C_i in K_i} a_i^T C_i a_i. If all q_i are finite, the sharp supremum over the unrestricted PSD cross-block completion class is (sum sqrt(q_i))^2. Combine marginal maximizing sequences with the construction above; attainment additionally needs attaining marginals. Under 0<=C_i<=G_i, choose C_i=G_i. Additional shared marginal constraints can make this formula an outer bound only; optimize the original joint class instead.

Unknown cross blocks do not supply a universal cancellation. If L=M=1 and epsilon=-eta, total variance is zero despite a positive calibration marginal contribution. Thus total covariance need not dominate M Gamma M^T. Conversely, if the admitted class includes block-diagonal Omega with fixed measurement/PV blocks and arbitrary Gamma, the unbounded family of Section 2 remains admitted and total variance is unbounded in every unprotected direction. This proves **unbounded possible total variance**, not unavoidable large variance in every actual joint law. Under this admitted unbounded marginal class, absent cross-block information supplies no finite uniform total bound. Fixed finite marginal covariances do permit the finite bound in Proposition 3 despite unknown cross blocks.

For a protected u, direct calibration displacement and all eta terms in that scalar's variance vanish. Its covariance with some other, unprotected scalar can still contain cross-block dependence. Protected from calibration is not protected from measurement, PV, selection, or physical-response uncertainty.

## 6. Tensor and statistical consumer

Keep the signed vector b and basis E_a. The covariance is the fourth-order tensor

    Cov(B_ij,B_kl) = sum_ab (C_b)_ab (E_a)_ij (E_b)_kl,
    B = sum_a b_a E_a.

For a test STF tensor U, u_a = U:E_a and Var(U:B)=u^T C_b u. Rotate components, maps, classes, and covariance together. For several depth bins or windows, stack the entire output and use the same Omega and latent channels; separately optimized window covariances are not one joint model. No cross-window law is created by a single-window M7.

The covariance-set consumer returns C_K(T)={T Omega T^T: Omega in K} and its support h_K(T^T H T), including extended-real +infinity. For affine PSD/linear constraints this is a standard semidefinite optimization problem. Closed-form Sections 2--5 are preferable when applicable. A numerical optimizer status or an unbounded-looking finite sequence is not a rigorous bound/certificate; an implementation needs checked primal feasibility and an outward dual upper bound, or an explicit feasible ray for unboundedness. A support function encodes the closed convex hull, not a stochastic law or arbitrary nonlinear images.

Covariance does not determine a law. Even centered scalar laws with variance one differ: equal mass at -1,+1 gives Pr(|X|>1)=0; mass 1/2 at zero and 1/4 each at -sqrt(2),+sqrt(2) gives 1/2. Consequently define a **set of qualified joint laws**, with an explicit covariance index and any additional distribution/response/mean assumptions:

    Lset = {(Omega, P): Omega in K,
            P is a qualified law for the declared joint state and response,
            its centered error block has covariance Omega}.

Gaussian sampling laws are extra assumptions. N(b_hat,C_b) is not automatically a posterior on the true tensor or physical state. If no qualified state law exists, the lawful output is a covariance or deterministic image set and the missing-law status, not a manufactured P.

For each qualified P apply one measurable joint map Psi to the same full state Z. It retains the tensor/path carrier x_phi, normalization/anchor policy Q, eligible fractions or occupancy F, all depth summaries, and any G_F. The family {Psi_# P : (Omega,P) in Lset} is a coupled law set; never combine a Q from one extremizing P with an F or G_F from another as if one draw produced them.

- Physical signed x_C = (sigma:sigma - omega:omega)/(6 H^2) + Omega_tilt + DeltaOmega_k retains the same-frame, rate/unit, curvature, tilt and nonzero-H premises from P1. With an axial vorticity vector, omega:omega = 2 omega_vec dot omega_vec. An optical magnitude STF covariance is not a source-qualified physical x_C law.
- A score Q=x/U needs its declared U>0 and domain; a tensor gauge needs its actual anchor body. Gamma_7 denotes a covariance here, not the P1 density-ratio parameter. No missing denominator is replaced by zero or a numerical floor.
- A sector fraction F=a/U is eligible only for justified 0<=a<=U, U>0. Spatial occupancy additionally requires a named support and measure. These definitions are distinct and must be tagged. Clipping a signed Q does not create either one.
- Pi_{P,q}(t)=P(q>t) is defined only under that named qualified measure and domain. For a law set its lower/upper envelopes are inf/sup over the same Lset; pointwise extrema at different thresholds need not form one attainable curve. Keep nested threshold events under one law. No Pi is generated from a covariance class alone.
- G_F uses the registered joint depth map; the P1 floored ratio max(F_comp,delta)/max(F_ref,delta), 0<delta<=1, is one example only after both fractions exist. A ratio of averages and an average of paired ratios are different targets. Cross-bin dependence remains explicit.

For a partially defined map, carry at least the defined image and the undefined-domain stratum. Under an actual P, report its undefined mass P(Z outside D_Psi) separately; do not renormalize it away unless conditional-on-domain inference is the declared target. Unknown but defined values and impossible/undefined values are different. Defined ratio images can be unbounded or disconnected as a denominator approaches zero, while values at zero stay undefined. Neither operation can be inferred merely from an unbounded covariance cone.

Confidence coverage is a sampling statement. If a valid C_Omega(Y) covers a common target under every qualified fixed Omega, then union_{Omega in K} C_Omega(Y) covers under whichever member is true, provided that member is in K. This does not furnish a measure inside the union, a Pi, or a physical response. All derived functional images inherit the same membership event only where their physical domain and response are justified. Bounded covariance alone also leaves mean, tail shape, likelihood, and physical identifiability unresolved.

## 7. Numerical qualifications and consuming decisions

The source response contract's scaled rank/algebra tolerance is 1e-10; saved-F checks are rtol=1e-9 and atol=1e-10. These are diagnostic numerical checks of that contract, not an exact-null proof. A tiny nonzero ||M^T u|| still has infinite variance supremum over unbounded Gamma. A singular-value cutoff must never turn a near-null direction into an exactly protected one without structural proof or a justified operator error bound plus a bounded covariance class.

For tr(Gamma)<=tau^2 and ||M-M_hat||_op<=epsilon, a valid sensitivity bound is

    Var_cal(u) <= tau^2 (||M_hat^T u|| + epsilon ||u||)^2.

This follows from the triangle inequality; epsilon is not inferred from two nominal/witness maps. If an admissible map class is supplied, a universally protected contrast must lie in intersection_M ker(M^T), and joint support is optimized over the same map/covariance choices. The two future representatives alone qualify only two conditional diagnostics.

| Available evidence | Permitted consumer conclusion | Remaining obstruction |
|---|---|---|
| No actual qualified M7 | General propositions and conditional contract only | Actual rank, contrasts, and support numbers unknown |
| Qualified M7, arbitrary PSD Gamma | Exact covariance cone; numerical rank diagnostic; structurally proved protected contrasts if available | No finite variance cap in unprotected directions |
| Qualified M7 plus source-qualified bounded Gamma class | Finite conditional calibration support, with units and class identity | Other marginals/cross blocks, means, response, and law |
| Qualified complete T and bounded joint Omega class | Conditional total covariance support | Coverage requires a valid sampling procedure; Pi requires a qualified state law |
| Qualified physical joint state/response/law and domains | Coupled physical-functional image/law analysis may be evaluated under its own acceptance | This note supplies none of those observational inputs |

The rank-full/unbounded-Gamma outcome would be useful negative information: within this linear calibration class, covariance shape alone cannot separate tensor uncertainty from calibration. It would not complete original H02, prove a physical degeneracy outside the declared model, establish a Bianchi family, or change any prior HOLD.

## Physics/math and claim audit

| Item | Owner / status | Evidence and boundary |
|---|---|---|
| Covariance cone, gauge correction, bounded-class support | common/obsstat mathematical interface; DERIVED | Explicit proofs; actual input-specific ranks absent |
| Full covariance and scalar marginal bounds | common statistical algebra; DERIVED / reused | Full PSD and cross-block assumptions; no empirical covariance |
| Tensor law-set consumer | htt for model-dependent laws; mio for diagnostic images; SPECIFIED | Preserves domains, joint dependence, and measure interpretation |
| Physical x/F/Pi/Q/G_F, empirical Gamma/PV | HOLD | No physical response/joint law/bounded source supplied |
| CAS, independent review, controller/publication acceptance | NOT PERFORMED / pending | No result promotion from this note |

No claim is upgraded in a repository ledger; no new mandatory field, gate, or permanent registry row is proposed. Required next work is the bounded lower-tier proof/finite-check task in `LOWER_PROOF_FINITE_CHECK_CONTRACT.md`, followed by fresh independent review. Actual data-operator consumption remains conditional on the separate seven-channel source contract succeeding.
