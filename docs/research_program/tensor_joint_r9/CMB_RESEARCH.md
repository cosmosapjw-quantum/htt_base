# CMB research: comparison certificates and response-law separation

> **Current revision 2**: report-seeded upgrade from `5e4e899c` on the `d514eabd` catalog base. Read [model-to-data design](revision2/MODEL_TO_DATA.md), [new derivations](revision2/THEORY_EXTENSION.md), and [revision review](revision2/REVIEW.md) first. The 30-node DAG preserves R9-00…23 and adds R9-24…29. Original R9 evidence below remains historical. This revision ran reference experiments, not production or observations; the original session had no GPT-6 archive. Research-only package acquisition/application was completed on 2026-09-13; see [current activation](revision2/harness_activation/STATE.md). The coding package and historical whole-run aggregate remain separate.

Scope: derived under the assumptions below; synthetic/exact algebra checks only. Source-specific details and exact fractional calculations are retained in the independent `cmb.json` research result. These methods do not change the 30 frozen R8 pools or their STOP_INVALID receipt.

## C1. Decide the rank inequality without solving every orbit distance

Let M exchangeable rows have a fixed permutation-equivariant score s_i equal to the kth other-row distance, k=ceil(sqrt(M-1)). Inclusive rank p=#{i:s_i>=s_0}/M is super-uniform under the admitted exchangeable experiment, including ties. Row-wise simulation independence is sufficient but not necessary; a signal/noise reuse scheme must establish the relevant joint exchangeability.

All pair distances have simultaneous certified intervals [L_ij,U_ij]. If the observed score lies in [a,b], a row i!=0 is certainly below it when at least k other-row upper bounds are strictly below a; it is certainly above or tied when at least M-k other-row lower bounds are >=b. Let B and H count these respective certified rows. Then

\[
p\in[(1+H)/M,(M-B)/M].
\]

Reject at alpha only when B>=M-floor(alpha M). Non-rejection is established when H>=floor(alpha M); otherwise return unresolved. These counts follow from kth-order-statistic inequalities, not distance point estimates. Computational pair selection may adapt to current bounds without changing the mathematical statistic. It must not adapt the target, sample rows, null law, alpha or score definition.

Use orbit-metric pivots before another global search: L_ij=max_v(0,L_iv-U_jv,L_jv-U_iv), U_ij=min_v(U_iv+U_jv). Combine these with existing bounds. Triangle reasoning applies to the actual **unsquared** quotient metric, because joint rotation acts isometrically on the fixed-scaled tensor carrier. It does not apply directly to squared distances, row-normalized changing metrics, or uncertified optimizer outputs. Threshold comparisons have a rational quaternion polynomial formulation on four compact charts; exact witnesses can settle strict upper comparisons and verified polynomial positivity can settle lower comparisons. This is an optional unresolved-comparison solver, not assumed cheap or already implemented.

The prototype checks 9 metric/order-statistic cases with retained ties and verifies enclosures against known Euclidean truth. It does not benchmark SO(3) speed or qualify actual Planck ranks. Production acceptance needs permutation tests, rational/oracle comparisons, interval-to-target binding, cumulative work accounting, and actual pipeline mocks. Strict deadline failure remains a resource failure; preserve old valid enclosures and use an explicitly new execution budget if continuing them.

## C2. A simple exact comparator is a separate scientific question

For fixed nonzero Q, the deterministic boost map B_Q: R^3 -> STF3 has rank three. Under the *ideal full-sky conditional null* O|Q~N(0,sigma3^2 I_7) in Frobenius-orthonormal STF coordinates, define f=||P_Im(BQ) O||^2/||O||^2. Independent orthogonal Gaussian sums give

\[
f\sim\mathrm{Beta}(3/2,2),\qquad
\Pr(F\ge f)=1-\tfrac52 f^{3/2}+\tfrac32 f^{5/2}.
\]

It asks whether O is concentrated in the fixed-Q boost-compatible subspace. It discards residual shape and is not the full Q/O morphology test or a velocity estimate. The null assumes Q and O independence/isotropy conditional on the declared Q experiment; mask, noise, foregrounds, same-sky component reuse and uncertain response violate a direct Beta substitution. R9 keeps full morphology as the primary family question; this comparator is a separately labelled sensitivity/ablation lane. If it becomes a co-primary empirical claim, declare its multiplicity allocation before inference instead of borrowing the frozen rank test's alpha after seeing results.

The 20,000-draw ideal-null fixture yields 1,021 rejections at 0.05; exact binomial 95% interval [0.04804,0.05419]. This corroborates a simple probability derivation, not a real-data qualification.

## C3. A deterministic boost map is not a noisy-sky conditional likelihood

In orthonormal harmonic coordinates, let source q and o be independent centred Gaussian multipoles with covariance C2 I_5 and C3 I_7. For a d=1 full-sky temperature boost, the infinitesimal real generator is skew-adjoint. If its q->o block is B_i, its reverse block is -B_i^T. To first order,

\[
q_{obs}=q-\beta_iB_i^T o+\cdots,\quad
o_{obs}=o+\beta_iB_iq+\cdots,
\]
\[
\partial_{\beta_i}\mathrm{Cov}(o_{obs},q_{obs})=(C2-C3)B_i,
\quad
\partial_{\beta_i} E[o_{obs}\mid q_{obs}=q]=(1-C3/C2)B_iq.
\]

Other independent neighbouring multipoles do not contribute to this particular cross-covariance at first order. The means must be centred and deterministic monopole/dipole components handled separately. At C2=C3 the conditional-mean derivative vanishes even though the fixed-source B_Q map retains rank three. A perfectly conditioned deterministic inverse therefore does not establish identifiability or precision under a stochastic sky. A noisy measured Q cannot silently become an error-free design matrix. Small Q also reduces absolute response strength regardless of condition number.

This is a direct linear covariance derivation using the established d=1 unitary property; no novelty claim is made for boost-induced covariance. [Dai & Chluba, arXiv:1403.6117, sections II–III](https://arxiv.org/pdf/1403.6117) provide the operator premise; abstract/introduction and the cited operator equations were checked in this run. These full-sky results do not certify processed cut-sky covariance.

The independent test exponentiates a synthetic 12-dimensional skew generator and differentiates the transformed joint covariance. Equal spectra give derivative residual below 3e-16; unequal spectra show second-order central-difference convergence (errors 8.50e-7,2.12e-7,5.31e-8). The arbitrary fixture B is not the full production boost matrix. A production likelihood must compose and differentiate the complete source/noise/processing law or justify a fixed-source conditional experiment.
