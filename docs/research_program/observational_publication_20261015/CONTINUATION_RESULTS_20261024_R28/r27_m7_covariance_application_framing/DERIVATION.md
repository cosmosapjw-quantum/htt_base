# Actual CF4 M7 covariance geometry and calibration fragility

Prepared 2026-10-24 by `/root/r27_m7_covariance_application_framing`; requested `gpt-6-astra/xhigh`, observed runtime `UNKNOWN`. Status: **DERIVED / CONDITIONAL application framing; actual consumer NOT RUN**. Owner: common/obsstat mathematical diagnostic, with HTT owning any later model-dependent inference. Transfer source: none. This note does not alter a campaign acceptance, original H02/H03, historical accounting, or a physical claim.

## Question and evidence

What covariance shapes and calibration budgets can the three accepted seven-channel CF4 responses produce in the entire five-dimensional signed magnitude-STF space, relative to the saved E1 estimator geometry?

The actual seven-channel result and its independent review now supply what the preceding generic derivation lacked: three signed 5-by-7 maps on the same 35,970 rows, five STF columns, 14 nuisance columns, and fixed E1 estimator. Their numerical ranks are reported as five at the inherited 1e-10 diagnostic threshold. This preparation only read matrix metadata and existing numbers; it did not certify exact ranks or run new sensitivity computations. INPUT.json binds the actual sources, reviews, generic candidate and allocation ancestry.

The distinct deliverable is the **data-specific calibration budget required to mimic the full E1 working covariance**, together with the five generalized sensitivity modes and all 28 independent covariance-channel response coefficients for each actual map. The earlier generic cone proofs and the report's Markov, worst-dependence, coupled-image and domain statements are reused. This is an application of standard algebra, not a foundational novelty claim or an exact statement about the unknown physical response.

## Domain and conventions

Use the released numerical maps M_s, s in {nominal, witness_round_nearest, witness_one_place_outer}, unchanged. They are conditional fixed-E1 derivatives, not measured physical shear maps or an exhaustive quantization class. Channel order is SNIa, FP, TFR, SBFm, SBFir, SNII, DirectCal; eta and b are in mag, M is dimensionless, Gamma is in mag^2. The direct channel is a common calibration-scale perturbation. Separate anchor measurement residuals stay in the unresolved residual block.

The signed optical carrier is B=sum_a b_a E_a in the saved Frobenius-orthonormal STF basis: diag(1,-1,0)/sqrt(2), diag(-1,-1,2)/sqrt(6), and the xy, xz, yz symmetric off-diagonal pairs divided by sqrt(2). Directions are observer-to-source J2000 equatorial directions. This is distinct from the apparent Hubble-rate carrier and the same-frame physical shear/vorticity rates in x_C. Retain metric signature (-,+,+,+) wherever those physical objects are discussed.

Let F_E1 be exactly the saved `source_comparisons.all.schur_fisher` (units mag^-2), and define C_ref=F_E1^-1 (mag^2). This definition supplies a working comparison geometry only; it does not assert that C_ref is the total empirical covariance, a posterior covariance, or a calibrated confidence region. The symbol F_E1 never denotes a filling fraction.

A stored JSON number is first parsed as binary64, then lifted exactly by its integer ratio. Exact statements below concern those dyadic M and F values. They do not certify the real-data operator before rounding, an uncertain producer map, or physical rank. The worker must establish exact symmetry/positive definiteness of the dyadic F; no silent symmetrization is allowed for this certificate.

## Full covariance image and finite certificates

For any fixed M, the previous derivation proves

    {M Gamma M^T : Gamma >= 0}
       = {C >= 0 : range(C) subset range(M)}.

A nonzero exact 5-by-5 minor of a 5-by-7 dyadic M certifies rank five for that finite computational input. Then the image is all S_+^5 and there is no nonzero protected output contrast. Set S=M M^T and R=M^T S^-1. The exact identity M R=I_5 supplies a concrete lift Gamma(C)=R C R^T for every PSD C. This is useful negative information: covariance shape alone does not distinguish arbitrary calibration covariance from tensor covariance within this fixed linear model. It says nothing about physical likelihood equivalence or signal means.

For every u != 0, v=M^T u != 0. Gamma_t=t vv^T/(v^T v) is PSD and gives u^T M Gamma_t M^T u=t v^T v, so its supremum is infinite without a cap. A tiny positive contraction is still unbounded under arbitrary Gamma.

The formal source-level common-shift identity is M7 1_7=0 and M6 1_6=-m_DirectCal. In the serialized matrices their residuals need not be exactly zero. Report both exact dyadic residuals and the already accepted floating diagnostics. Do not subtract a common-mode component or round the residual to zero. A right-null channel gauge is not a left-null output protection. The formal quotient and the unmodified dyadic input are separate mathematical objects.

## The new observable: budget to reproduce the working covariance

For any target C>=0 and full-row-rank M, the canonical lift

    Gamma_*(C)=R C R^T

minimizes tr(Gamma) among PSD lifts of C. Indeed with P=R M the orthogonal channel-row-space projector, every lift satisfies P Gamma P=Gamma_*(C), and the orthogonal complementary block adds nonnegative trace. A zero complementary block forces its cross block to vanish, so the minimum-trace lift is unique.

Consequently compute, for each actual map,

    t_match = tr(Gamma_*(C_ref)),     tau_match=sqrt(t_match).

Here t_match is in mag^2 and tau_match in mag. It is the **smallest hypothetical total channel-variance budget that can reproduce C_ref exactly in this linear model**. It is not an estimate of the catalogue's calibration uncertainty. Preserve the full signed Gamma_* and its induced C_ref, including off-diagonal entries. The associated physical covariance remains unknown.

For the spectral class 0<=Gamma<=t I, the analogous minimum cap to reproduce C_ref is t_spec_match=lambda_max(Gamma_*). This follows because the fixed compression P Gamma P=Gamma_* implies ||Gamma||op>=||Gamma_*||op, and Gamma_* attains that minimum. Its numerical value may be reported as a diagnostic, with the exact matrix witness and congruence identity retained.

The arbitrary Loewner-cap criterion is C_ref<=M G M^T, for an externally supplied G>=0. The consumer must expose the complete linear map in G:

    C(G)=sum_i G_ii m_i m_i^T
         +sum_(i<j) G_ij (m_i m_j^T+m_j m_i^T).

Save all 28 symmetric 5-by-5 coefficient matrices. An off-diagonal coefficient need not itself be PSD; it is a derivative of a covariance map, not an independent covariance. This representation retains every channel correlation without supplying invented G entries.

## Bounded-class full-tensor profiles in the E1 metric

Let F_E1=R_F^T R_F, with R_F the transpose of its lower Cholesky factor. Put W=R_F M and H=W W^T. Its five positive eigenvalues lambda_1>=...>=lambda_5 (units mag^-2) describe the full-rank response in working-normalized coordinates. Store H and eigenprojectors/directions, not only lambda_1 or a norm. Degenerate eigenspaces have no unique individual mode; numerical eigenvector signs are conventional.

For fixed s and t=tau^2>=0:

| Calibration class | Whole output image / diagnostic |
|---|---|
| Gamma>=0, unbounded | S_+^5 after exact rank-five certification |
| Gamma>=0, tr Gamma<=t | C>=0 with tr(R C R^T)<=t |
| 0<=Gamma<=t I_7 | 0<=C<=t M M^T |
| 0<=Gamma<=G, G>=0 | 0<=C<=M G M^T |

Both trace and spectral classes have directional bound t ||M^T u||^2 and largest possible working-normalized eigenvalue t lambda_1. Their maximum total working-normalized variance differs:

    sup_trace tr(F_E1 C)=t lambda_1,
    sup_spectral tr(F_E1 C)=t sum_i lambda_i.

Thus t_first=1/lambda_1 is the smallest trace/spectral cap at which one working-normalized contrast can reach variance one. It is a comparative fragility scale, not a significance threshold or recommended empirical cap. Plot against z=tau/sqrt(t_first), a declared dimensionless sensitivity coordinate, and show the three actual representatives separately. The curves z^2 and z^2 sum(lambda_i)/lambda_1 are parameterized scenarios. The spectral covariance matrix t M M^T is simultaneously attainable, while the trace class generally cannot attain all its directional maxima together.

The minimizing full-covariance lift and the first-mode threshold answer distinct questions; report both. For rank below five, C_ref is outside the image, so t_match=+infinity/INFEASIBLE and no inverse S is used. A partially successful exact-rank computation is UNKNOWN, not a tolerance-based rank theorem.

## Conditional full-tensor confidence construction and its actual HOLD

The report already derives Markov/Gaussian ellipsoids under a covariance envelope. The specialization here shows what assumptions would connect that construction to M7 while retaining arbitrary cross dependence.

Write a *declared statistical model* b_hat=b_true+mu+r+M eta with E r=E eta=0, finite second moments, a deterministic mean bias mu in a declared set B_mu, and a jointly PSD covariance of (r,eta). The five-dimensional r is the pushforward of **all remaining** measurement, selection, PV, optical-remainder and separate-anchor residual terms under a source-qualified decomposition. It is not the released total covariance added a second time. Suppose, additionally,

    Cov(r)<=G_r,  Cov(eta)<=G,  G_r>=0, G>=0,

with arbitrary cross covariance compatible with joint PSD. For any fixed a>0, Young's inequality applied to each projected centered fluctuation gives the common envelope

    Cov(r+M eta) <= V_a=(1+a)G_r+(1+1/a)M G M^T.

This bound does not delete or estimate the cross block. It is conservative; no simultaneous extremizer is asserted. Under a trace cap tr Gamma<=t, G=t I is a valid common envelope, not a feasible trace-class matrix when k>1. If V_a>0, E[e^T V_a^-1 e]<=5. For alpha in (0,1), the region

    C_alpha(Y)={theta: exists mu in B_mu,
       (b_hat-theta-mu)^T V_a^-1 (b_hat-theta-mu)<=5/alpha}

has coverage at least 1-alpha for every fixed law satisfying those assumptions. Proof: center by the true mu, use the expectation identity and Markov inequality; the true mu is in the union. If e is additionally jointly Gaussian after the linear map, replace 5/alpha by the chi-square_5 1-alpha quantile. Gaussianity is an added sampling premise; this is not a posterior on theta. V_a and a must be prespecified or otherwise validly uniform, not optimized after looking at successful data coverage.

For singular V_a, impose e in range(V_a), which follows from centered covariance domination; restrict the centered residual to that range and use the Moore-Penrose quadratic with r=rank(V_a) and r/alpha. Null-space coordinates are exact constraints. If r=0, the centered error is zero almost surely and the region is b_hat-B_mu; do not use a zero-degree chi-square numerical convention. Unknown or unbounded B_mu may yield no informative finite region.

A complementary fixed-metric Markov bound uses no common matrix maximizer. If G_r=lambda^2 C_ref, lambda>=0, and tr Gamma<=t, the L2 triangle inequality gives

    E[e^T F_E1 e] <= (sqrt(5)*lambda + sqrt(t*lambda_1))^2.

This is a conservative joint-error expectation bound, not a sharp claim for the full cross-block class. With a known B_mu, dividing that bound by alpha gives a full five-dimensional ellipsoid in F_E1. For calibration alone (r=0) the expectation coefficient t lambda_1 is the exact support value. This bound is theory-only here: neither lambda, B_mu nor actual finite-moment controls have been measured.

Actual CF4 output must therefore say `HOLD_MISSING_TOTAL_MEAN_COVARIANCE_RESPONSE_ASSUMPTIONS`; it must not print numerical physical confidence, Pi, p-values or posterior mass from these formulas. The data product provides M and a working metric, not G_r/G/B_mu, the PV map, or a law.

## Coupled functional and domain boundary

One common qualified tensor/state region may be mapped jointly through (x,F,Pi,Q,G_F) only with their actual response, measures, denominators, supports and depth relation. An optical magnitude STF region is not the physical x_C state. No rate, H, vorticity, tilt or curvature is inferred here. F requires a justified eligible sector or occupancy measure; Pi requires a named qualified law; G_F requires supported depth bins and their joint dependence. The single-window M7 result supplies none of those missing inputs. The report's saved four-window apparent measure remains a different carrier and is not retrofitted with this calibration covariance.

For any future partial map Psi, retain the image on D_Psi and the undefined-domain stratum. Do not clip, floor an unregistered denominator, remove undefined mass, attach independent per-functional extremizers, or normalize a confidence set into a law. Covariance-cone unboundedness does not establish unbounded physical functionals on a restricted physical domain.

## Literature and overlap audit

Reused local material: the preceding covariance-cone DERIVATION.md Sections 2--7; REPORT_20261024_REV1/sections/07_mathematical_details.tex (covariance domination, sharp scalar dependence, pseudoinverse limits); P1_SELECTED_TENSOR_LAW_20261024/sections/02_identification.tex, 05_coupled_functionals.tex and 07_proofs.tex (tensor basis, common coverage image, physical nonidentification, named coupled measures and domains). These files were read directly. The new consumer's actual M7/F_E1 coefficients, t_match, t_first and full 28-coefficient map were not present there.

Primary external sources checked 2026-10-24:

- Vandenberghe, Boyd and Comanor, *Generalized Chebyshev Bounds via Semidefinite Programming*, SIAM Review 49(1), 52--64 (2007), [author publication page](https://web.stanford.edu/~boyd/papers/prob_bnds.html). It places mean/covariance-constrained probability bounds in standard convex-optimization theory. This note uses an elementary conservative Markov construction, not that paper's optimality claim.
- Bertsimas and Popescu, *Optimal Inequalities in Probability Theory: A Convex Optimization Approach*, SIAM J. Optim. 15(3), 780--804 (2005), DOI 10.1137/S1052623401399903, [author-hosted paper](https://www.mit.edu/~dbertsim/papers/MomentProblems/Optimal-inequalities-in-probability-theory-A-convex-optimization-approach-SIAM15.pdf). The published first page and definitions distinguish moment-feasible distributions and tight probability optimization. Covariance constraints select a set of laws rather than one distribution.
- Boyd and Vandenberghe, *Convex Optimization* (2004), PSD cone and pseudoinverse background were already verified by the preceding source note. A fresh web attempt at its author-hosted PDF timed out; no new successful fetch or byte identity is claimed.

No mathematical priority, literature novelty, universal CAS validation or physical scientific admission is claimed. Exact finite algebra, numerical consistency and an independent review of the future actual result remain separate evidence stages.

## Audit conclusion and next decision

Assumptions, units, signs and singular strata are explicit. The useful next action is the bounded actual-data consumer in CONTRACT.md. No repository claim ledger is changed by this framing. Existing H02/H03 and physical-functional holds remain; the parent continues other authorized branches after either the actual consumer's scoped result or an exact residual HOLD.
