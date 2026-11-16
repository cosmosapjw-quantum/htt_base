# R54 mathematical and physical audit

Audited revision: `77f61c17ba33ff28ff4f16a7d42621d8041e5ce4` of `cosmosapjw-quantum/htt_base`.
Review provenance: independent child agent `/root/proof_review`, supplied raw statements and no suspected findings; prior `INDEPENDENT_REVIEW.json` was read only after the derivations below. No repository file or result was mutated. This is a bounded theorem/derivation review, not a certification of the complete manuscript or its observational likelihood.

**Verdict: correct only after the stated restrictions and local corrections.** The Gaussian sufficiency, confidence-cylinder, convex-duality, representation-theory and two-kernel arguments mostly survive. T3(iv) is false as written; T5 is undefined on part of its declared domain; `rho_ratio` returns NaN at valid large optical depth; the constant-velocity model in T9 is a restricted tilt history, not a general definition of global tilt.

## Findings requiring changes

1. **PRV-01, major, T3(iv), lines 80–82:** “and its width does not shrink with data” is false. Let `(iota,nu)` have a proper nondegenerate Gaussian prior with covariance `[[1,r],[r,1]]`, `0<r<1`, and let the likelihood measure only `iota` with precision `n`. Then
   \[
   \operatorname{Var}(\nu\mid y)=1-r^2+\frac{r^2}{n+1},\qquad
   \partial_n\operatorname{Var}(\nu\mid y)=-\frac{r^2}{(n+1)^2}<0.
   \]
   At `r=0.9`, the two-sided 95% marginal interval width changes from `3.91993` (`n=0`) to `2.01271` (`n=10`) to `1.70902` (`n=10000`). The conditional variance `Var(nu|iota,y)=1-r²` is unchanged. Thus data can contract the marginal via a prior correlation, while the data likelihood remains flat along the kernel. The previous review finding R54-A1-06 was marked fixed but its replacement retained this error.

   **Minimal replacement:** “For any interval procedure with finite endpoints for every observation, uniform frequentist coverage on the unrestricted parameter space is zero. The posterior conditional law of nu given iota is its conditional prior. Marginal intervals for v.theta can shrink as iota is learned; their residual uncertainty depends on this conditional prior.” A proper prior does not force *every* possible credible interval to be bounded (one-sided credible intervals are an immediate exception); specify the finite-endpoint two-sided procedure when using T3(ii). Replace the overly absolute consequence “never about the data” by “cannot provide a data-only bound uniformly along the likelihood-equivalence class.” T3(i)–(iii) are otherwise supported by the stated Gaussian model.

2. **PRV-02, moderate, T5, lines 113–118 and `wishart_gls_factors`:** `n>p-k+1` does not imply that `S` is invertible. Example `n=2,p=k=3` satisfies the printed premise but every covariance from two 3D Gaussian draws has rank at most two. The actual function accepts this input and returns all factors as one even though the defined GLS uses `S^-1`.

   **Minimal correction:** add `Sigma` positive definite and `n>=p` for integer simulated-covariance degrees of freedom (equivalently `n>p-1` for a nonsingular general Wishart), retain `n>p-k+1` for the moment, and reject inputs outside that domain in both factor helpers. For the square case, `theta_hat=J^-1 y` can be separately extended without `S^-1`, but its Hotelling statistic still needs nonsingular `S`; do not silently use this extension to justify the written inverse formula. The second-moment derivation itself is correct on the corrected domain.

3. **PRV-03, moderate, `rho_ratio`:** `sqrt(6)*(exp(.7*tau)-1)/(exp(.7*tau)+6)` returns NaN at `tau=1100,10000`; the exact result tends to `sqrt(6)`. This is a numerical implementation error on the physical `tau>=0` domain, not a failure of T8.

   **Minimal correction:** `sqrt(6)*(-expm1(-.7*tau))/(1+6*exp(-.7*tau))`, with finite nonnegative optical-depth validation and tests at zero, tiny positive values, and large optical depth. The existing tests stop at tau=30 (plus a finite recombination grid) and do not protect this limit.

4. **PRV-04, major interpretation restriction, T9 lines 284–293 and THEORY_LOOPS L6:** “A global tilt is the linear hypothesis V_j = V for all j” is valid as a **constant-velocity tilt submodel**, not as a definition covering all spatially homogeneous tilted cosmologies. Homogeneity constrains spatial dependence at fixed cosmic time; it does not fix time evolution along the observed light cone. For a freely moving nonrelativistic test congruence on FLRW, conserved comoving momentum gives `v(a)~a^-1`, so a homogeneous tilt has `V(z)=(1+z)V0`. The same-shell closure identity remains exactly valid at first order while the constant-V fit fails. This example does not assert a self-consistent single-fluid tilted Bianchi-I solution; it only demonstrates the distinction between homogeneity and constancy in time.

   **Minimal correction:** label the present fit `constant_velocity_global_tilt` throughout and retain its numerical result. For a declared dynamical family fit `V_j=T_j lambda`, with transfer/selection averages over each shell or count population, and report the design rank. The residual dimension is `n_obs-rank(D)` (equal to `3(n_c+n_d)-3` when the stated design has rank three and the effective covariance is nonsingular). A rejection of the constant model is not a rejection of all global-tilt histories. The algebraic closure and the stated constant-model degrees of freedom pass.

5. **PRV-05, moderate domain/claim restriction, T8(iv) and consequence (1):** the projection formula for a least `L²(I)` norm requires `K_T,K_E in L²(I)` and a positive-definite Gram matrix. An arbitrary interval with positive scattering does not by itself imply this; e.g. an unbounded interval with optical depth approaching a finite limit has nondecaying kernels and divergent Gram integrals. The finite interval/grid used by the code satisfies the necessary restriction. Also “every upper limit ... a family with at most two parameters ... or a sign restriction” is too exhaustive: other declared shape/norm/dynamical constraints can control the nullspace.

   **Minimal correction:** state a finite interval with nonzero length and finite optical depth for (iii-a)/(iv), or explicitly require square-integrable kernels and invertible Gram. Replace the consequence by “an upper norm bound requires additional restrictions controlling the kernel of the two-functional map, such as a specified low-dimensional dynamical family, a sign restriction, or an explicit physical budget.” Arbitrarily scaling the mathematical kernel is a statement about the unconstrained linear function space; the admissible perturbative regime must still be imposed before interpreting arbitrarily large histories physically.

## Obligation matrix

| Claim | Mathematical assessment | Scope / remaining input |
|---|---|---|
| T1 | proved as written in the fixed known-C Gaussian model | exact-likelihood envelope, not a claim about approximate computational methods |
| T2 | proved as written | known nonsingular C; support-cylinder simultaneous coverage; nonlinear images have at least nominal coverage |
| T3(i–iii) | proved as written | unrestricted parameter space and stated measurable events |
| T3(iv) | refuted | PRV-01 gives a proper Gaussian-prior counterexample |
| T4 | proved for a nonempty closed convex Theta and a convex body K0 | Sion/bipolar application; empty Theta must be excluded |
| T5 | correct after domain restriction | PRV-02; second moments are not an exact Gaussian posterior law |
| T6 | proved under O(3) equivariance and its stated first-order homogeneous/local-tensor setting | no scalar response of an axial spin-1 source; no general no-go for finite-wavelength or structured Bianchi backgrounds |
| T7a | proved under corrected per-sample R4 span and stated two-depth-group condition | generic variable depths alone are not the sufficient condition stated in the theorem |
| T7b | correct for rigid rotation with free frame spin | physical calibration of the astrometric frame must be independent of the removed same-source spin |
| T7c | proved | known positive-definite cross-depth covariance and declared g |
| T8(i–iii,v) | proved for nonnegative optical depth and well-defined weighted moments | sign changes understood a.e.; physical families are a subset of the unconstrained function space |
| T8(iv) | correct after function-space restriction | PRV-05 |
| T9 | identity and constant-model dimension proved | PRV-04 restricts physical interpretation |
| L1 | conditional mean-bias identity proved | logarithm of expected regional slope; finite-catalogue random fitted slopes are not equal to that mean |
| L2 | angular integral and integration-by-parts structure checked | state momentum/mass energy-unit conventions and vanishing boundary term; no external source priority check here |

## Reproducible evidence

`proof_checks.py` reads the exact git object for `r54_identifiability.py`, extracts the two relevant function definitions via Python AST, and evaluates them without modifying the repository. It writes `proof_checks.json`. Command: `python /workspace/scratch/ca5a06f498ba/proof_checks.py` (exit 0). This is a focused counterexample execution, not a run of the entire repository test suite.

Independent Wolfram Language evaluation returned exactly:
`posterior_nu_variance=(1+n-n*r^2)/(1+n)`, derivative `-r^2/(1+n)^2`, conditional variance and limit `1-r²`, and rank two for the singular 3x3 sample covariance. No four-engine claim is made.

Full text read: THEOREMS.md (361 lines), THEORY_LOOPS.md (195 lines), tests/r54/test_r54_theorems.py, `r54_identifiability.py`, root and HTT package AGENTS, physics/xqpi skills. Existing review history was then checked for prior treatment. Raw observational maps, full CF4 pair sums, native Bianchi transfers and complete publication manuscript were not audited here.

## Publication implication and constructive next calculation

The theorem bundle provides a useful organizing account of what the owned observables can identify, but it does not establish a new information-gain method: the sufficiency tie is classical, and the representation/sign-change arguments are elementary consequences of specified structures. It can support a methods/application paper only with a concrete result that standard scalar summaries obscure—for example a component-resolved confidence set, its nuisance-dependent rotations and null directions, and a transparent cross-depth compatibility test with inherited covariance.

Use the existing carrier to compute a **nuisance-robust identified tensor set** and a **calibration sensitivity threshold**. Keep the same data, covariance and forward response in the direct GLS/score baseline and the five-view report. Show equality of likelihood ratios, then quantify what the five views make explicit (unbounded directions, axis instability, policy-normalized support intervals), rather than claim extra statistical power. The local/global comparison should include declared evolving `T(z)` families when an existing calibrated transfer is available; otherwise leave that family unresolved and report the constant-V submodel only. This is a finite physical interpretation task; it does not require another general audit cycle.
