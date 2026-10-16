# HTT SIX-PAPER P1/S01: signed and partially defined functional contract

- Date: 2026-10-16 KST
- Parent: `cosmosapjw-quantum/htt_base` PR #542, commit `1d9222ec72401dfc9140a8fd146bd79a6135ea3f` (stacked branch; do not merge `main`).
- Authority: `docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json`, blob `6c37984188f93fee398496d297032652ec5c58f5`, 6 papers/42 nodes.
- Selected task: P1/S01, depends on scoped E3. This document is **R5 bounded derivation**, not an observational measurement or P1 paper submission.
- Comparison: source formalism `SCIENTIFIC_SCOPE_KO.md` blob `b139211af4f128ee43400571d3fa43100f155e3e`; PR066 pushforward blob `d51422f5a5a02402ddde92138b0ce72aef84b34f`; MIO filling-fraction blob `9190b3d653b19ab12375151b5a7075ddb596a4c2`.
- Signature `(-,+,+,+)`; one common normal/frame/congruence `u^a`, epoch, normalization `H=Theta/3` with `H != 0`. `c` is not set to 1; H and shear/vorticity have `s^-1` and their contractions `s^-2`. Dimensionless densities use one explicitly stated convention.

## 1. Signed geometric projection and sector-specific normalizers

For the specified Gauss projection and fixed physical convention:

`x_C = (sigma_ab sigma^ab - omega_ab omega^ab)/(6 H^2) + Omega_tilt + DeltaOmega_k`.

This is **signed**. Neither nonnegative projection nor data identification follows from the formula. The shear normalization is `U_sigma = 3 B_sigma^2/2 > 0`, with registered, dimensionless shear-sector MES bound `B_sigma`; define `Q = x_C/U_sigma` only where the bound is positive and the convention/source are supplied. Since total `x_C` includes tilt, curvature and vorticity, `U_sigma` is **not** a certified ceiling for `x_C`; `Q` can be negative or exceed 1. These are admissible values, not automatically a detected physical inconsistency. `H=0` is outside this normalized coordinate; return undefined, not zero or infinity.

Distinct `F` is defined **only for an independently certified nonnegative sector** `a` and a positive admissible ceiling `U` satisfying `0 <= a <= U`: `F = a/U`. The sector, ceiling status, common units/comparator/frame and input hashes must be source bound; an unqualified signed `x_C` is not an `F` numerator. Neither clipping negative `x_C` nor filling a missing ceiling is allowed. `F` is not volume occupancy, a physical Bayes probability, or bolometric `F4 = <(T/T0)^4>`. `G_F` is a further depth contrast and is not `F` or `Q`.

For specified two different depth bins and common sky support, selection, covariance, normalization and frame, predeclare `delta in (0,1]` and define

`G_F = exp(log(max(F_comparison,delta)) - log(max(F_reference,delta)))`.

It is positive, and (for F in [0,1]) satisfies `delta <= G_F <= 1/delta`. The floor limits sensitivity but is a **new analysis choice**, not a physical reidentification. We report both a log contrast and its value; extremely small `delta` can cause machine overflow and must fail closed rather than silently yield `inf`. Different source depths/normalization/covariance are not exchangeable.

## 2. Sharp pointwise completion envelope for a partial pushforward

Let a normalized *joint* sample measure on distinct persistent draw IDs be `mu=sum_i p_i delta_(z_i)`, `p_i >= 0`, `sum_i p_i=1`. Let `f(z_i)` be known on index set `K` and unmeasured/undefined on `U` (disjoint). Maintain two separate missing reasons: value **unmeasured although the functional is defined**, versus **domain not certified** (e.g. H=0, missing certified ceiling, frame mismatch). The latter need not admit any physical completion; treating it as a completion is **only a mathematical uncertainty envelope**, not an inferred posterior on the non-domain.

For the fixed registered functional `f in {Q,F,G_F}` and predeclared real threshold `t`, the known exceedance mass is `a_t=sum_{i in K} p_i 1[f_i > t]`, strict `>` excludes ties, and missing mass is `u=sum_{i in U} p_i`. For completely unrestricted completion of every missing event, the sharp scalar bounds are

`Pi_f(t) in [a_t, a_t + u]`.

**Proof:** Each missing Bernoulli indicator has a value in [0,1], so its total contribution is between zero and `u`. Assign all missing indicators false or all true to attain the two endpoints. If a physical domain/range restricts completions, those bounds are conservative outer bounds and may not be sharp. No **defined-only renormalization** by `1-u` is legitimate for the full-sample probability without an additional missingness/exchangeability law. If `u=1`, the interval is [0,1]. If `u=0`, the interval collapses to the usual empirical pushforward.

A useful stricter statement: for ordered thresholds `t1 < ... < tm` and a **single common completed scalar value** per unknown draw, the exceedance indicators are nonincreasing across thresholds. Thus `Pi(t_j) >= Pi(t_(j+1))`. The independent rectangle product of marginal intervals is in general an **overapproximation** to the attainable joint curve set. For fixed discrete unknown draw masses and deterministic completions, attainable curves are weighted sums of threshold-prefix binary vectors; allowing each missing draw an arbitrary conditional probability law convexifies this set. Never fit thresholds as independent data points or multiply their likelihoods.

For source-dependent coupled functionals `Q_i`, `F_i`, `G_i`, use **one identical sample ID and original weight**; missing sets can differ by functional. Nine signal-processing products from one sky are never nine independent cosmological draws.

## 3. Independent counterexample and coverage limit

Take three weighted draws `A=.2`, `B=.3`, `C=.5`. For `Q` let `Q_A=-.8`, `Q_B=.5`, `Q_C` undefined because one physical sector is missing. At `t=.2`, `a_t=.3`, `u=.5`, so `Pi_Q(.2) in [.3,.8]`. The tempting defined-only conditional exceedance `.3/(.2+.3)=.6` is **not** a posterior probability of the full sample. At `t=.5`, the tie for `B` is excluded, yielding `[0,.5]`. Retaining negative `Q_A` is essential.

For an admissible `F_B=.4` but unknown/inadmissible `F_A,F_C`, the missing set changes: `Pi_F(.2) in [.3,1]`. A numeric `F=0` fabricated for missing A,C would misrepresent zero as observed. This counterexample does not assert a physical x posterior or real Planck/CF4 functional measurement.

## 4. Source/literature and claim boundary

Existing PR066 `PosteriorPushforwardSample` accepts only finite Q, F, G_F, x_C and globally normalizes all weights; it is valid **on a completely defined finite sample**. The S01 typed partial layer will not mutate that frozen API or consume MIO certificate/report payloads. It must gate unknown values, reject mismatched sample IDs/source identity, enforce registered depth/floor/ceiling and reproduce the known-only limit.

Partial-identification intervals have established precedent, especially Charles F. Manski, *Partial Identification of Probability Distributions* (2003) and “Partial identification with missing data: concepts and findings” (journal metadata not verified here; primary URL `https://www.sciencedirect.com/science/article/pii/S0888613X04001124`). The pointwise bound is elementary and **not** asserted as a novel theorem. The proposed cosmology-specific contribution, if any, would require source-bound conditional identification and empirical sensitivity in S02–S04.

Evidence status: **derived** for the formulas and sharp pointwise envelope; **not yet implementation-verified** at this stage. No observed data likelihood, physical geometry posterior, Planck anomaly p-value or journal-submission gate has been opened. S01 remains pending until coded validation and source/readback.
