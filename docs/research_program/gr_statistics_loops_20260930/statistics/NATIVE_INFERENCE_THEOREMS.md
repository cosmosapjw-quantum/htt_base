# Native-observation inference for the free-intercept optical first jet

Date: 2026-09-30. Status: **derived candidate; independent decision pending**. This note proves finite-sample coverage and identification limits for a specified observation law. It reports no CF4, Union3, or other catalogue fit. Generic Gaussian confidence-set inversion is standard; novelty of this particular physical target and synthesis is **unestablished**.

The physical target is the acceleration of a specified smooth source/test congruence at the observation event. Geodesicity is a tested restriction. Neither the target nor its statistical rejection identifies self-consistent pressureless matter, a preferred cosmological slicing, or a global Einstein solution.

## 1. Physical variables, conventions, and claim boundary

Use signature (-,+,+,+), physical velocities U=c u and O=c o, u.u=o.o=-1, and observer tetrad o=(1,0,0,0). Coordinates have dimensions of length. A sourceward direction n is unit spatial and K=-o+n. The supplied geometric results give

    Z0(n) = ζ0 + ζ·n,      ζ0 = sqrt(1+|ζ|²),
    H(n) = h0 + h1·n + h2:nn,       h2 symmetric trace-free,
    u = (ζ0,ζ),
    S00=h0,  S0i=-h1i/2,  Sij=h2ij,
    B = S + S(u,u)g,       A_a = 2c B_ab u^b.                 (1)

The physical parameter x=(ζ,h0,h1,h2) has dimension 12. ζ and Z0 are dimensionless; h0,h1,h2,B have units s^-1; A has units m s^-2. Always convert H in km s^-1 Mpc^-1 consistently before using c and distances. B(u,u)=0, so A.u=0 and a(x)=sqrt(g^{ab}A_a A_b) is real and nonnegative. Acceleration components must all refer to the declared observer tetrad.

Define the pointwise geodesic null

    G = {x : B_ab(x)u^b(x)=0}.                              (2)

It has three independent constraints, not four. At fixed u, the admissible symmetric B tensors form the nine-dimensional space B(u,u)=0. In a u-rest tetrad, B00=0 and the map B→Bu has three freely specifiable components B_i0. Thus its rank is three; Lorentz changes of tetrad preserve that rank. The optical lift S↔B is an isomorphism at fixed u. Therefore G is a smooth nine-dimensional submanifold of the full 12-dimensional physical parameter space. This dimension count does **not** supply a chi-square likelihood-ratio calibration.

Inputs (1) and the finite-distance envelope below come from `../gr/OPTICAL_THEOREMS.md` and `../gr/FINITE_DISTANCE_THEOREM.md`. Their first-jet realization is kinematic. Actual galaxies need not be exact samples from one smooth source field extending to the observer; this is a scientific hypothesis requiring a declared coarse-graining/tracer interpretation.

## 2. Native redshift and distance-modulus contract

For a fixed selected list of N objects, take their directions n_i as known. Let r_i>0 be the latent **true area distances**, in a stated length unit. Write

    Z_i = Z0(x,n_i) + (r_i/c)H(x,n_i) + ρ_i > 0,
    m_zi = Z_i - 1,
    m_μi = 5 log10[r_i Z_i²/(10 pc)].                        (3)

The logarithm is dimensionless: r_i and 10 pc must use the same units. The second equation for the modulus requires metric null propagation, the appropriate reciprocity theorem and photon conservation/transparency, so d_L=r_i Z_i². It also requires that the delivered distance indicator really measures the corresponding luminosity-distance modulus. This must be audited separately for each tracer and catalogue. Additive zero-point offsets belong in a declared calibration model, not in the definition of r_i.

Use the actual native vector y=(z_obs, μ_obs), or a different documented measurement vector with its correct forward map. Do not replace r_i by a modulus-derived point estimate and then condition on it as exact. Do not transform noisy observed z into d_A and silently discard the induced cross-covariance/non-Gaussianity. Merely switching to native observables does not prove their errors Gaussian.

For the theorem in Section 4, assume exactly

    y = m(θ*) + F β* + ε,       ε ~ N_m(0,C),                (4)

where θ includes x, the latent r_i, admissible ρ_i, and any additional nonlinear nuisance parameters; m=2N in (3). F is a fixed, known m×q matrix and β* is arbitrary. Nuisance means lie in the fixed subspace col(F). Examples are a shared distance-modulus zero point or prespecified tracer-specific zero points; their corresponding redshift rows in F are zero. C is a known positive-definite covariance of the **whole** observation vector, with consistent block units. Independent redshift and modulus blocks are a special case, not a default. Duplicate objects, shared calibration, group velocities and intrinsic scatter can create correlations. An exactly known Gaussian extra scatter can be included in C; unspecified velocities or systematics cannot be declared to be such scatter without evidence.

Equation (4) can be conditional on a fixed ancillary design D, provided the conditional Gaussian law, C(D), and F(D) are correct and the true θ remains admissible. It then yields conditional and unconditional coverage. Catalog selection using noisy redshift, flux, modulus, or data-dependent outlier rejection generally changes this conditional law. It is not handled by calling the realized catalogue a fixed design. A selection-aware likelihood may be used in the general inversion construction of Section 7, with a separately calibrated acceptance rule.

If calibration nuisance effects are nonlinear or have restricted values, they can remain in θ. Projecting an unrestricted linear superset is valid but may discard information. C estimated from this y, a guessed diagonal covariance, non-Gaussian tails, or an unmodelled selection rule invalidate the exact claim unless a new proof/calibration is supplied.

## 3. A deterministic admissible remainder set

Fix external bounds Kc≥0 and M2≥0, both length^-2, and L>0, with their physical interpretation stated. On every actual ray segment 0≤s≤L assume the optical tidal operator norm is at most Kc and |d²Z/ds²|≤M2, using the affine normalization K(0)=-o+n. Put

    η(s)=sinh(sqrt(Kc)s)/(sqrt(Kc)s)-1,
    η(s)=0 when Kc=0,             ηL=η(L)<1.

One conservative enlarged parameter domain Ω permits 0<r_i≤L(1+ηL) and

    |ρ_i| ≤ E_i(x,r_i)
           = M2 r_i²/[2(1-ηL)²]
             + |H(x,n_i)| r_i ηL/[c(1-ηL)].               (5)

Every true catalogue satisfying the full-segment hypotheses and (3) lies in this domain. Indeed GR-FD gives r_i≤s_i(1+η(s_i))≤L(1+ηL), s_i≤r_i/(1-ηL), and the displayed remainder bound. A tighter necessary domain adds latent s_i∈(0,L] with

    s_i[1-η(s_i)] ≤ r_i ≤ s_i[1+η(s_i)],
    |ρ_i| ≤ M2 s_i²/2 + |H(x,n_i)|s_iη(s_i)/c.             (6)

Either domain is an **outer approximation** to the set realizable by one smooth spacetime/congruence along all rays. Sufficiency of (5) or (6) for a common finite-distance physical realization has not been proved or used. Feasibility means compatibility with this enlarged inference class, not construction of a global physical universe.

These are full-segment assumptions, not numbers inferred from small endpoint multipoles. Choosing small Kc,M2 after looking at residuals loses the stated coverage. A prespecified sensitivity grid can report separate conditional conclusions. To be valid whenever any one of several declared scenarios is true, take the **union** of their confidence sets. Intersecting them asserts all scenarios simultaneously and has no such guarantee. Bounds obtained from a separate confidence procedure with failure probability δ give at least 1-α-δ coverage by the union bound; independence is unnecessary, but a valid bound procedure is necessary. Unrestricted remainders can make the method uninformative.

## 4. The finite-sample projected residual theorem

Let W=C^(-1/2), any fixed whitening matrix with WCW^T=I. Let P be the Euclidean orthogonal projector onto col(WF)^⊥. Its rank is

    ν = m-rank(F).

For 0<α<1 and ν>0, let qν,α be the (1-α) quantile of χ²_ν. Define

    Q_y(θ) = || P W [y-m(θ)] ||²,
    Cα(y) = {θ∈Ω : Q_y(θ)≤qν,α}.                         (7)

**Theorem N1 — finite-sample coverage and nuisance elimination.** Under (4), fixed C,F, and θ*∈Ω,

    Pr_{θ*,β*}{θ*∈Cα(y)} = 1-α,                           (8)

uniformly in β*. Moreover,

    Q_y(θ) = inf_β ||W[y-m(θ)-Fβ]||².                     (9)

If ν=0 set q=0; Cα=Ω and coverage is one. No fitting-parameter count is subtracted from ν.

**Proof.** Since PWF=0, at the true θ the projected residual is PWε. Wε has m independent standard normal coordinates. Choose an orthogonal matrix that diagonalizes the symmetric idempotent P, with ν ones and m-ν zeros. Rotational invariance of the standard Gaussian gives Q_y(θ*) as the sum of squares of precisely ν independent standard normals. This proves (8), including uniformity over β*. For (9), orthogonally decompose v=W[y-m(θ)] into Pv and (I-P)v. The second component lies in col(WF), and can be cancelled by WFβ; the first is orthogonal to every WFβ. Pythagoras therefore gives the minimum ||Pv||², attained by at least one β. For ν=0, P=0 and Q vanishes for every θ. □

The χ² law is for the residual at the **true complete θ**, after removal of the specified fixed linear nuisance space. It is not a claim that min_θ Q_y(θ) has a χ² law. Latent distances, nonlinear normalization, bounded remainder parameters and boundary cases need not be regular or identifiable. They do not alter the proof, but can make the set very broad. This is a standard Neyman inversion with a Gaussian pivot, not a new generic statistical principle.

**Corollary N1a — physical projections and simultaneous statements.** Define

    Xα={x(θ): θ∈Cα},   Aα={A(x(θ)): θ∈Cα},
    Iα={sqrt(g^{ab}A_a A_b): θ∈Cα}.

Then the true x, A, and acceleration norm are contained in these sets jointly with probability at least 1-α. The same event gives simultaneous coverage for every prespecified deterministic function of θ. Infimum/supremum intervals enclosing Iα retain coverage, including infinite endpoints.

**Proof.** θ*∈Cα implies containment of each of its deterministic images; taking probabilities proves the result. Projection can add coverage, hence the inequality rather than equality. □

## 5. A valid geodesicity decision and the empty-set safeguard

Define Cα,G={θ∈Cα:x(θ)∈G}. Use these mutually distinct reports:

1. Cα nonempty and Cα,G empty: **geodesicity rejected within the declared observation/remainder model**.
2. Both nonempty: **geodesicity not excluded by this confidence procedure**.
3. Cα empty: **declared model class incompatible at this acceptance threshold**; do not call this acceleration detection.
4. Feasibility or exclusion not certified: **computationally unresolved**.

**Theorem N2 — size control.** Under every true parameter satisfying (4), θ*∈Ω and x*∈G, the probability of report 1 is at most α. Under every true parameter in Ω, the probability of report 3 is at most α. More strongly, the union of reports 1 and 3 has probability at most α under a true geodesic parameter.

**Proof.** On θ*∈Cα, the set Cα is nonempty. Under the null, θ* also belongs to Cα,G. Thus each erroneous event, and their union under the null, is a subset of {θ*∉Cα}. Apply (8). □

Rejecting A=0 means the selected congruence is incompatible with pointwise geodesicity under the declared measurement and smoothness assumptions. It does not establish a force law, show that galaxies form non-geodesic conserved dust, or reject general relativity. A nonzero observer-frame H dipole alone is insufficient: boosts and source acceleration must be separated through (1), including the absolute intercept.

A feasible point with Q≤q certifies nonemptiness. Null exclusion requires a rigorous lower bound inf_{Ω∩G}Q>q, or another verified proof of infeasibility. Failure of a local optimizer to find a null point is not that proof. Infimum equality q can be inconclusive if the infimum is not attained. Compact parameter boxes give attainment only when the domain and objective are also closed/continuous there; arbitrary boxes can destroy coverage unless independently justified. A confidence set of sampled solutions is an inner approximation and cannot establish coverage or null exclusion. A certified outer enclosure can. A strictly positive lower bound on Iα is sufficient for exclusion; exclusion of zero need not imply a positive infimum for a noncompact set.

## 6. Oracle identification: angular sampling and radial leverage

This section is an optimistic diagnostic with **known true r_i, zero remainder, no calibration nuisance**, using redshift means alone. It is not a claim about the identifiability of the native latent-distance model. Let E4 have rows (1,n_i^T). Choose any real basis of degree≤2 spherical polynomials, with E9 its N×9 evaluation matrix, containing the degree≤1 basis. Let D=diag(r_i/c), all r_i>0. The unconstrained linear coefficient design is

    X = [E4, D E9]                                         (10)

with 13 columns, before the one physical intercept normalization.

**Theorem N3 — exact rank criterion.** X has rank 13 iff E4 has rank 4, E9 has rank 9, and

    col(E4) ∩ col(D E9) = {0}.                             (11)

Equivalently, rank(E4)=4 and rank[(I-P4)D E9]=9, where P4 projects onto col(E4). In particular N≥13 is necessary for this unconstrained full-rank criterion.

**Proof.** For any matrices A,B, dim(col(A)+col(B)) equals rank(A)+rank(B)-dim(col(A)∩col(B)). D is invertible, so rank(DE9)=rank(E9). Substituting A=E4,B=DE9 proves the first characterization. Orthogonal projection kills col(E4), and adds precisely the directions of col(DE9) modulo that subspace, proving the equivalent characterization. □

**Constant-radius failure.** If r_i=R>0, then col(E4)⊂col(DE9), so rank X=rank E9≤9. For unisolvent directions (rank E9=9), each admissible intercept ζ may be changed to another ζ′ while compensating

    H′(n)=H(n)+(c/R)[Z0(n)-Z0′(n)].                       (12)

This leaves all redshift means on that radius unchanged and remains within degree≤2. The admissible intercepts form a three-dimensional hyperboloid, yielding a genuine three-dimensional family of physically normalized degeneracies. Therefore angular coverage alone does not separate an absolute intercept from its slope.

**Radial spread is necessary for full recovery, but not sufficient.** Even with unisolvent sky directions, take

    r_i=R/(1+ε n_iz),       0<|ε|<1.                      (13)

For every degree≤1 polynomial p(n), the product (1+ε n_z)p(n) has degree≤2 on the sphere. Hence p(n_i)=(r_i/R)[(1+ε n_iz)p(n_i)], so col(E4)⊂col(DE9) again and rank X=9. Distances vary with direction, yet all four unconstrained intercept directions remain confounded. This is a radial-angular aliasing counterexample with strictly positive distances.

**A sufficient design with 13 observations.** Take nine unisolvent directions at one radius R1>0. Repeat four of those directions at a distinct positive radius R2, choosing the four so their E4 submatrix has rank 4. Then rank X=13. To prove this, a zero linear combination in the first nine rows means its degree≤2 polynomial vanishes at nine unisolvent directions and hence identically. Thus its slope polynomial equals -(c/R1) times its intercept polynomial. At the four repeated directions, the remaining equation is (1-R2/R1)p(n)=0. Rank four and R1≠R2 force p=0, and then the slope vanishes. Two full unisolvent angular shells are another sufficient, nonminimal design. Nearby sufficiently small perturbations of either full-rank design remain full rank by continuity of a nonzero minor.

**Physical and nuisance qualifications.** In the physical chart ζ0=sqrt(1+|ζ|²), the N×3 intercept Jacobian is

    Jζ = Ndir + 1(ζ/ζ0)^T,
    Jphys=[Jζ, D E9].                                     (14)

Full rank X implies rank Jphys=12, since this chart has rank three. The converse need not hold: a one-dimensional kernel of X transverse to the hyperboloid tangent can leave Jphys rank 12. Rank 12 is a sufficient local injectivity condition by selecting a nonsingular 12-row submap and applying the inverse-function theorem; rank deficiency alone does not establish a global nonlinear nonidentifiability theorem. At constant R and unisolvent directions, rank Jphys=9 and (12) supplies the stronger exact degeneracy proof. If fixed linear redshift nuisances are also removed, use rank(PWJphys); a nuisance space can absorb physically useful modes. The physical 12-column local condition needs N≥12, unlike the sufficient unconstrained 13-column diagnostic.

Formal full rank is not adequate precision. Small singular values of a dimensionlessly scaled design diagnose weak radial leverage. Changing units rescales columns, so report the chosen scales and preferably the full singular spectrum, not a bare condition number.

## 7. Native-model identification limits and extensions

**Theorem N4 — positive-slack remainder gives local partial identification.** Fix a finite noiseless native mean vector produced by a parameter θ* with r_i>0,Z_i>0. Suppose each remainder satisfies strict slack |ρ_i*|<E_i(x*,r_i), E_i is continuous near x*, and x* is an interior point of any further physical-parameter restrictions. Then there is a neighbourhood of x* in the physical chart such that every x in it produces the same native mean vector for an admissible remainder choice, keeping r and calibration fixed.

**Proof.** Hold each true Z_i and r_i fixed. For another x define

    ρ_i(x)=Z_i-Z0(x,n_i)-(r_i/c)H(x,n_i).

This is continuous and equals ρ_i* at x*. Since finitely many inequalities have strict slack and the E_i are continuous, all remain valid in a sufficiently small common neighbourhood. Z_i, r_i and consequently both components of (3) are unchanged. □

Thus a bounded first-order remainder ordinarily defines a partially identified region even with noiseless finite data. Small confidence regions require actual information and restrictive scientifically justified envelopes; the confidence theorem alone supplies neither. N4 does not preclude rejecting a geodesic null that lies outside the entire identified region.

**Distance-scale invariance.** If a common free modulus offset κ is present and the domain admits the transformation, then for a>0

    r_i′=a r_i, H′=H/a, ρ_i′=ρ_i, ζ′=ζ,
    κ′=κ-5log10 a                                       (15)

leaves both native means unchanged. It sends B′=B/a and A′=A/a. Therefore an external absolute distance calibration is required for an unrestricted absolute acceleration scale. For fixed Kc,M2,L the admissible domain need not be invariant; do not assert a global invariance through fixed external bounds. It is exact for the unconstrained measurement map, and applies within any admitted pair of transformed points. Joint rescaling Kc′=Kc/a²,M2′=M2/a²,L′=aL preserves (5)-(6), showing why freely rescaled bounds do not break it. The null A=0 is invariant for finite a. If arbitrarily large a are allowed, acceleration norms can approach zero without reaching it, reinforcing the infimum caveat above.

**General native likelihood inversion.** Gaussianity is optional for the logical construction. If a fully specified family p_θ,β for selected native data admits acceptance regions R_θ,β with Pr_θ,β(y∈R_θ,β)≥1-α, then the set {(θ,β): y∈R_θ,β} and all its projections have ≥1-α coverage. Proof is the definition of each acceptance region followed by the containment argument of Corollary N1a. Uniform treatment or projection over nuisance β is essential. Selection-aware truncated likelihoods, non-Gaussian distance-indicator likelihoods, and uncertain covariance need their own calibrated R; they do not inherit the χ² threshold in (7).

For a deterministic covariance uncertainty set S that is known to contain C*, a union of valid sets Cα,C over C∈S retains ≥1-α coverage, because the union contains Cα,C*. If S covers C* with probability ≥1-δ, the same event-intersection argument gives ≥1-α-δ under valid fixed-C* calibration. This is a formal robust extension, not an implemented CF4 covariance solution; choosing S requires external evidence and the union may be uninformative.

## 8. Relationship to primary prior work and publication claim ceiling

The following pinned primary versions were inspected on 2026-09-30; this is a targeted comparison, not an exhaustive priority search.

- Kalbouneh et al., *The anisotropic expansion rate of the local Universe and its covariant cosmographic interpretation*, [arXiv:2510.02510v1](https://arxiv.org/html/2510.02510v1), §§2, 6.3 and Appendix A: CF4 plus Pantheon+, harmonic maximum-likelihood fitting; Pantheon+ uses covariance information while CF4 measurement correlations are assumed absent. They discuss a low-redshift breakdown of their dust/continuum interpretation. Their Appendix A explicitly fits logarithmic redshift-to-luminosity-distance angular coefficients from distance moduli. Harmonic fitting, covariance weighting, and cosmographic anisotropy inference therefore cannot be claimed here as new.
- Maartens et al., *Covariant cosmography: the observer-dependence of the Hubble parameter*, [arXiv:2312.09875v3](https://arxiv.org/html/2312.09875v3), §2.1 equations (2)-(5) and §§4.1-4.3: defines a dust matter frame, obtains zero matter acceleration from momentum conservation, and studies observer-dependent redshift/distance cosmography. The present unrestricted source-congruence target differs by allowing acceleration before testing it; this difference does not establish publication priority.

Potentially useful synthesis to investigate: infer the absolute intercept and first slope jointly from native noisy observables, retain certified finite-distance remainder uncertainty, reconstruct A by (1), and test the three geodesicity restrictions without first imposing dust. The exact inversion theorem is deliberately elementary and conservative. A JCAP-level method claim additionally needs: an adequate broader primary-literature novelty audit, defensible tracer/native-likelihood contracts, demonstrably useful identification and power, validated numerical set computation, and catalogue-specific systematic/selection treatment. None is claimed complete by this note.

## 9. Reproducible later local analysis recipe — not executed

1. Freeze exact catalogue releases and hashes; inspect documentation and schema. For CF4 and Union3 separately record native observable definitions, redshift frame, distance calibration, covariance ordering, duplicates/cross-catalogue overlap, masks, selection and prior corrections. The user has these data; no bytes or data-specific likelihood were inspected in this loop. Pantheon+ prior work is not evidence about the Union3 input contract.
2. Freeze a source-congruence/tracer interpretation, observer tetrad, units, whether distance duality applies to each delivered quantity, and the treatment of peculiar velocities. State which corrections would remove the physical signal of interest.
3. Declare C,F and the selected-data sampling law; if the Gaussian fixed-C premise is not warranted, choose an alternative native acceptance construction. Add external calibration data as observations when appropriate rather than quietly fixing κ.
4. Declare physical bounds/rapidity ranges only when independently justified. Fix Kc,M2,L and the domain (5) or (6), or a finite sensitivity family. Set α and the intended geodesicity report before inspecting fits.
5. Implement m(θ) and analytic derivatives using (1)-(3). Treat r_i as latent positive quantities. Compute P through a rank-revealing QR/SVD of WF and ν=m-rank(F), without subtracting nonlinear parameter counts. Check oracle design diagnostics only as diagnostics, not identification proofs for latent noisy data.
6. Find feasible physical and geodesic points, then compute certified enclosures/lower bounds if an exclusion claim is sought. Record parameter domain, units, tolerances, all solver certificates, and whether a minimizer is attained. Report unresolved optimization honestly.
7. Validate the actual implementation against the fixed-law χ² pivot and constructed constant-radius/radial-aliasing cases with a small approved synthetic check; this note has executed no numerical or catalogue suite. Assess power and envelope sensitivity only under an explicitly authorized simulation plan.
8. Deliver the four-way decision in Section 5, projected acceleration/norm sets, calibration dependence, remainder sensitivity, and which assumptions are externally established versus hypothesized. Any real-data finding is conditional on that complete contract.

## 10. Evidence record

Owner derivations: N1-N4, projection/null corollaries, scale invariance, and the algebraic design counterexamples. Independent helper checked the oracle design algebra and supplied the stronger radial-angular aliasing example (13) and 13-row sufficient design; it did not make a final independent decision on this candidate. Literature-supported: dust/geodesicity premises and earlier anisotropic harmonic inference. No observation fit, runtime calibration, covariance reconstruction, universal identifiability proof, or priority finding. Final promotion is reserved for an independent reviewer.
