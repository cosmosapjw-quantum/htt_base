# Independent review of the theory-integrated R9 research plan

Verdict: **confirmed**

Review scope: a developed, source-supported, feasible research-plan revision. This verdict is not production, formal, empirical, or novelty validation. Reviewed draft: `/workspace/scratch/99299f5cbe0c/HTT_R9_Theory_Integrated_Research_Plan_v1_KO.md`, final inspected SHA-256 `693124110dca7dc642e6181e091134ababedeb4d51f76db4115f96671ed407b4`, as read during this review on 2026-09-12 UTC. This reviewer edited no original source or plan, and executed no experiments or production functions. The author applied the focused corrections below, which this reviewer then inspected.

## Rationale

The principal proposal is supported. Historical candidate statements improve R9 by making observable-law equivalence, target-specific information loss, legitimate shared calibration, full-tensor orientation, and conditional physical realization explicit completion targets. These map to real consumers in the existing 24-node R9 DAG and retain the original low-multipole morphology / local boost versus matter tilt / signed-sector motivation. The plan does not mistake 172 source sections for independent proved theorems and explicitly preserves the catalog's `NOT_ESTABLISHED_FOR_THIS_PROPOSAL` status. It also preserves the existing branch-specific formal and empirical requirements without making a complete catalog census or BASS solver a common prerequisite.

Two small but substantive corrections were identified and resolved during review: one avoids a false inference from zero local information, and the other removes an apparent dependency that contradicts R9 branch isolation. A subsequently added minimax statement received an explicit zero-distance qualification. No further correction is required at this research-plan scope.

## Mathematical checks

1. **NT2-A2.** The pinned excerpt explicitly claims convergence for any decaying response. Setting `r_l=1/l` gives `(2l+1)r_l²/2=1/l+1/(2l²)`, which diverges by harmonic comparison. The draft correctly distinguishes a local Fisher-tail criterion from global approximate sufficiency. Its `r_l=O(l^-p), p>1` sufficient condition is correct for the stated ideal weighted sum.

2. **NT2-A3.** The pinned excerpt explicitly asserts `p_global >= max_i p_local,i`. For the draft's three mock rows and observed score, the inclusive `+1` ranks are exactly `(1/4,1)` locally and `1/4` globally. Its analytic independent-uniform check also gives `1-.99²=.0199`, below `.9`. This refutes the ordering without refuting a correctly exchangeable max-rank test. The revision makes that distinction correctly.

3. **Strengthened T2′.** The original manuscript assumes positive denominator but does not require nonnegative numerator. For `N=-2+s`, `D=2-s`, `s in [0,1]`, the ratio is identically `-1`; the independent product-image upper endpoint is `-1/2`. Yet the coefficient product is `-1`. This directly contradicts the original upper-endpoint iff rule. Set inclusion remains true. The proposed sign-aware corner comparison or support of `N-qD` on a compact domain with denominator bounded away from zero is a sound replacement direction.

4. **Two-block Fisher expression.** With `C0=diag(C2 I5,C3 I7)` and the stated skew generator, the derivative has off-diagonal blocks `(C2-C3)B_i` and its transpose. The two trace blocks each contribute the same inner product, cancelling the Fisher factor `1/2`. Thus the draft's coefficient `(C2-C3)^2/(C2 C3) tr(B_i^T B_j)` is correct. The equal-spectrum cancellation is correctly limited to this first-order two-block covariance contribution; it is not an actual processed-sky admission.

5. **Robust mean-set distinction.** Compactness makes zero set distance imply attained overlap. The scalar discrepancy formula `max(|Delta theta|-2 rho,0)` is correct, and the draft explicitly limits the Gaussian simple-hypothesis power formula instead of assigning it automatically to composite sets.

6. **Shared state and physical interpretation.** The projection/intersection inclusion, dependence-robust alpha accounting, covariance-orthogonality qualification, first-order amplitude versus second-order invariant warning, and normal-congruence/vorticity separation are correctly stated at planning scope. They do not establish physical endpoint realization, and the draft does not claim that they do.

7. **Added compact-convex Gaussian discrimination result.** For positive set distance, the supporting hyperplanes through the nearest means reduce the worst-case Gaussian test to the nearest simple pair. This establishes minimax maximal error `Phi(-delta/2)`. The Neyman–Pearson bound for that pair and its supporting-hyperplane test give the stated uniform error-budget condition `delta >= z_(1-alpha)+z_(1-gamma)`. The final version explicitly requires nonempty compact-convex sets and `delta>0` for the separating construction. At zero distance it separately states the overlap lower bound and attainability by a randomized fair-coin test. Thus the previously undefined unit direction is no longer used at overlap. The bounds `0<alpha,gamma<1/2` make the targeted nontrivial discrimination regime explicit.

8. **Added information-loss identity.** In the stated regular experiment and fixed statistic, the summary score is `E[s(Y)|T]`. Total covariance therefore gives `I_Y-I_T=E[Cov(s(Y)|T)]`, a PSD matrix. The draft correctly requires nuisance-adjusted information to be recomputed for each summary and does not equate this local identity with global sufficiency.

## Corrections identified and resolved

**R1 — Zero local information is not structural nonidentifiability.** The initially inspected Section 5 completion sentence labelled an exact null `unidentified` next to the efficient Fisher discussion. A null score/tangent must be distinguished from equality of full probability laws. The analytic check `Y ~ N(theta^3,1)`, `theta in R`, gives `I(theta)=9 theta^4`, so `I(0)=0`, while different theta values have different laws. **Resolution inspected:** the final text reports weak local information and zero first-order information separately, reserves `unidentified` for an admitted-law equivalence or constrained-fibre witness, and includes this analytic example. A response-kernel null gives the stronger conclusion only within the explicitly fixed linear law and an admissible nontrivial fibre.

**R2 — Preserve independent jet intake in the diagram.** Section 10's initial edge `F --> J` visually made the later additional-observation design a prerequisite for the jet/remainder input. Canonical R9-19 requires only `SEED` and permits an independently supplied analytic/external conditional response. **Resolution inspected:** F-to-J is now explicitly optional input, and the accompanying paragraph says the diagram shows where research outputs are used, does not add global gates, allows existing qualified jet inputs without waiting for F, and scopes candidate amendments to the statements each branch actually uses.

**R3 — Qualify the newly added zero-distance minimax case.** The first added paragraph used a nearest-pair unit vector without separating `delta=0`. **Resolution inspected:** nonempty mean sets, the positive-distance construction, overlap and randomized attainability, and nontrivial alpha/gamma domains are now explicit. The added result is supported at its stated Gaussian convex-set scope.

## Source and review coverage

Directly read the full draft; `RESEARCH_RECORD.md`; R9 `THEORY.md`, `CMB_RESEARCH.md`, `DESIGN.md`, `SCIENTIFIC_CONTRACT.md`, and the 24-node `campaign_dag.json`; the full strengthened-theorem manuscript; the full catalog JSON structure and the source-qualified NT2-A2, NT2-A3, T-A3 excerpts; and the catalog/math agents' reports plus exact-counterexample output. Candidate mappings were cross-checked against the existing R9 consumers and preserved source roles. This review does not claim to have proved or exhaustively classified all 172 candidate sections, retrieved every archive member, revalidated historical runtime evidence, or independently checked the entire external literature.

The author can deliver the inspected version as a reviewed research-plan revision. Novelty, actual data-law qualification, numerical coverage, production admission, and GR sharpness remain explicitly outside this verdict.
