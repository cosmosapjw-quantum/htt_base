# Independent decision: statistical follow-up

Date: 2026-09-30. Reviewer: `/root/gr_independent_decision`, a separate agent from both statistical proposers. This review is independent of proposal authorship and does not modify the earlier 18-claim GR decision. It is an analytical proof review, not a catalogue analysis, simulation calibration, certified implementation, or exhaustive novelty audit.

**Decision: all 12 bounded claims below receive PROMOTE_ANALYTIC_CONDITIONAL.** Their probability laws, nuisance spaces, parameter domains, physical target, and observation kernels are part of the accepted statements. Actual CF4/Union3 closure, empirical usefulness, numerical certification, and publication novelty remain unestablished. No full scientific numerical suite or automatic Wilks approximation is required for these analytic proofs.

## 1. Reviewed inputs and first findings

The actual frozen manuscripts and claim ledgers were read: `statistics/NATIVE_INFERENCE_THEOREMS.md`, `statistics/STATISTICAL_CLAIMS_NATIVE.json`, `statistics/INFORMATION_LIMIT_THEOREMS.md`, and `statistics/STATISTICAL_CLAIMS_INFORMATION.json`. The supporting exact-arithmetic files `evidence/morphology_check.wl` and `.json` were examined. The previously reviewed GR inverse and finite-distance certificate supply the physical identities; they are not inferred afresh from statistical fits. Input hashes are in the companion JSON.

The reviewer independently recomputed the morphology fractions, the scalar geodesicity identity, Gaussian invariance argument, cutoff derivatives and numerical constants, Gaussian confidence pivot, nuisance minimization, design aliases, and distance-scale transformation. The morphology CAS output was supporting evidence only. The primary paper [Kalbouneh et al., arXiv:2510.02510v1](https://arxiv.org/html/2510.02510v1) was opened directly for context; its existing multipolar and alignment analysis prevents treating orientation-aware cosmography itself as new. This bounded review makes no claim to have independently reread every source cited by the proposers.

| First finding | Resolution retained in the final decision |
|---|---|
| N4's remainder slack alone would not remove other parameter boundaries. | The proposer added the necessary hypothesis that the true physical parameter is interior to further restrictions. A relative-neighbourhood formulation would also suffice. |
| Exact coverage is a law at the true complete parameter, not at a fitted minimizer. | N1 uses only `m-rank(F)` projected-noise coordinates and subtracts no nonlinear parameter count. Accepted as written. |
| Model emptiness and geodesic-null exclusion are different conclusions. | N2 preserves nonempty alternative, nonempty null, empty total model, and computationally unresolved reports. |
| Absolute distance-scale freedom changes acceleration magnitude but preserves the zero null. | N-SCALE explicitly permits null exclusion with acceleration infimum zero in an unbounded domain. |
| Separate sector powers and the power of a combined radial field are different summaries. | STAT-INFO-1–3 are restricted to separate powers; combined power can retain the missing cross term. |
| The cutoff construction might have been mistaken for an acceleration ambiguity. | Both constructed fields are constant near the observer and have zero local slopes. STAT-INFO-4–5 concern source value/intercept continuation only. |

## 2. Native inference: exact accepted statements

| Claim | Accepted statement and assumptions |
|---|---|
| N1 | Under the exact native law `y=m(θ*)+Fβ*+ε`, `ε~N(0,C)`, known positive-definite joint `C`, fixed nuisance matrix `F`, fixed admissible domain containing truth, and positive residual rank, inversion of the projected residual at the stated chi-square quantile covers the complete true `θ*` with exactly `1-α` probability, uniformly in `β*`. Rank zero gives coverage one. |
| N1a | Every stated deterministic physical projection of this confidence set contains its true image jointly with probability at least `1-α`. Projection may be broad or unbounded. |
| N2 | Under a true geodesic parameter, the probability of reporting nonempty total set but empty null intersection is at most `α`. Total model emptiness has probability at most `α` under any admitted truth. Under a geodesic truth the union of those two error events also has probability at most `α`. |
| N3 | In the known-distance, zero-remainder, no-calibration oracle model, the unconstrained 13-column design has full rank exactly under the stated column-space condition. The constant-radius and radius–direction aliases, the 13-row sufficient design, and the distinction from physical local rank 12 are valid. |
| N4 | Within the declared finite-object envelope model, strict remainder slack, envelope continuity, and interiority to other physical restrictions permit an open neighbourhood of physical first jets with identical noiseless native means, holding distances and calibration fixed and adjusting remainders. This is not a common-spacetime realization theorem. |
| N-SCALE | Whenever both transformed points are admitted, scaling `r→a r`, `H→H/a`, and the common modulus offset by `-5 log10(a)` preserves native means and sends `A→A/a`. Fixed external segment bounds may obstruct global scaling. Zero acceleration is invariant for finite positive `a`; an unbounded scale orbit can approach zero norm without containing zero. |
| N-GENERAL | Inverting genuinely calibrated acceptance regions gives the stated general-law coverage; projection over nuisance and unions over admitted uncertainty scenarios preserve it. A domain or covariance confidence failure probability `δ` gives the stated `1-α-δ` bound under valid fixed-truth calibration. |

### Independent proof checks

Let `W C W^T=I` and let `P` be the orthogonal projector onto the complement of `col(WF)`. At the true complete parameter, the nuisance term vanishes and the statistic is `||PWε||²`. Orthogonal diagonalization of the fixed idempotent projector gives exactly `rank(P)=m-rank(F)` independent squared standard normals. No regularity, identifiability, or interior condition on the nonlinear mean parameter is used by this pivot. The Pythagorean decomposition into `col(WF)` and its complement also proves exact minimization over unrestricted linear nuisance coefficients. It does not give a chi-square distribution for minimization over the full nonlinear model.

The true-parameter containment event simultaneously supplies all physical projection coverages. Under a true null, that event also supplies a feasible null point. Thus null exclusion and total-set emptiness imply noncoverage, proving N2 and its union statement. No independence between these error events is assumed.

For N3, the rank identity is the dimension formula for a sum of column spaces. At one radius, changes in the physically normalized intercept can be compensated exactly by a degree-one change in slope. For `r_i=R/(1+ε n_iz)`, multiplying any degree-one intercept polynomial by `1+ε n_z` stays within degree two, so even varying radii can retain the same alias. For the proposed 13 observations, the first nine unisolvent rows fix the slope polynomial in terms of the intercept; four independent repeated directions at a second radius force that intercept polynomial to vanish. This proves full rank. None of this identifies unknown noisy distances in the native model.

For N4, preserving each true `Z_i` and `r_i` preserves both native redshift and modulus means. The required new remainder is a continuous function of the perturbed physical coefficients. Finitely many strict inequalities remain true in a common sufficiently small neighbourhood. The added interiority condition covers the other parameter constraints. This conclusion belongs to the enlarged envelope class; the envelope constraints were only proved necessary for a common finite-distance physical model.

### Coverage conditions that are not empirical findings

The native model correctly retains latent true area distances and computes the luminosity-distance modulus from the true endpoint redshift. This avoids declaring a transformed noisy distance exact, but it does not prove native Gaussianity. The exact theorem still requires a justified full covariance, fixed nuisance space, source/tracer interpretation, calibrated distance indicator, distance duality when used, valid selection law, and externally defensible full-segment remainder bounds.

Treating a selection based on noisy observations as an ancillary fixed design is invalid without an appropriate conditional law. Estimated covariance does not inherit the known-covariance pivot automatically. Freely chosen remainder bounds after inspecting residuals do not inherit the frozen-domain guarantee. The confidence theorem can be perfectly valid and nearly uninformative if the admitted nuisance or remainder class is broad.

To report rejection, a feasible alternative point and certified null infeasibility are needed. A local optimizer's failure is insufficient. Inner samples of a confidence set are insufficient for coverage or exclusion. An outer enclosure may support exclusion only together with the appropriate feasibility certificate and rigorous enclosure relation. Noncompactness matters: excluding zero need not produce a strictly positive acceleration lower bound. Compactness plus closedness and continuity, or another explicit separation argument, can restore that implication.

## 3. Information limits: exact accepted statements

| Claim | Accepted statement and assumptions |
|---|---|
| STAT-INFO-1 | The explicit two admissible local test-source tuples have identical five separate-sector powers but zero versus nonzero acceleration. They are not asserted to solve the same Einstein–matter closure. |
| STAT-INFO-2 | On the admissible optical image, `J_geo=(Su)^2+[S(u,u)]²=(Bu)^2=A²/(4c²)≥0`, with equality exactly at zero acceleration. The displayed sky-coordinate expression retains the needed relative contractions. |
| STAT-INFO-3 | Under the specified independent isotropic Gaussian coefficient blocks, the two tuples induce identical joint separate-power laws. Every test measurable only in these powers has the same rejection probability at the two points, whereas the full-data KL divergence is positive as displayed. |
| STAT-INFO-4 | For any `M>0,a>0`, the constructed globally smooth future unit test fields in fixed Minkowski spacetime have identical complete exterior optical data, obey the same bound `|Z''|≤M`, and have origin rapidity separation `min(1,Ma²)/25`. The observer is fixed independently of the source field. |
| STAT-INFO-5 | When the entire observation kernel and nuisance distribution depend only on those common exterior data, any confidence set covering both points at level `1-α` has the stated diameter-probability and expectation floor; the stated two-point estimator-risk floor also holds. |

### Morphology and the scalar repair

Independent arithmetic gives the rotated tuple's `q/H=377/128`, `b/H=(-765,1275,-600,0)/512`, and `b²/H²=87525/16384>0`, agreeing with the supporting evidence. The initial tuple has `Bu=0`. Only the slope dipole changes direction; the separate norms stay fixed. This is not a common rotation of the entire sky. In particular, the intercept–slope dipole contraction changes, and a combined radial-field norm can detect that cross term.

Writing `b=Su+q u_flat` and using `u²=-1` proves `b²=(Su)²+q²`. Since `b.u=0`, positivity of the timelike vector's rest space proves that vanishing norm means `b=0`; there is no nonzero null-vector loophole. The sky formula has matrix `I-vv^T/γ²`, whose eigenvalues are `1,1,1/γ²`, confirming positivity directly. This scalar diagnostic is outside the separate-power sigma-algebra. It refutes any claim that all scalar summaries necessarily lose the relevant information.

For each Gaussian block, an orthogonal rotation carries one mean to the other and preserves both the isotropic noise law and the squared norm. Independence yields equality of joint compressed laws. The changed dipole has squared mean difference `2(15H/8)²`, giving KL `225H²/(64σ_p²)`. The full-data simple-versus-simple error tends to zero as that noise scale tends to zero. No uniform boundary-alternative consistency or real-survey isotropy is implied.

### The fixed-bound cutout construction

For the quintic cutoff, `max|F'|=15/8` and `max|F''|=10/√3`. Rescaling gives the derivative bounds `15/(4a)` and `40/(√3 a²)`. Positive unit-integral mollification preserves these bounds and the range, with an inner constant plateau. Consequently the radial spatial composition is smooth at the origin as well as across the transition.

The stationary boost field gives `Z=coshχ+n_x sinhχ`; differentiating twice yields the upper bound `e^δ(|χ''|+|χ'|²)`. Substituting `δ=min(1,Ma²)/25` gives a ratio to `M` bounded by `e^(1/25)[8/(5√3)+9/400]`. The rational certificate is correct: `e^(1/25)<25/24` and `√3>12/7` imply an upper bound `1147/1152<1`. Thus the fixed derivative bound is genuinely respected; this is not an arbitrarily sharp bump with uncontrolled derivatives.

Both fields equal the observer field outside the cutoff and the metric is unchanged, so endpoint redshift and area distance agree exactly. They are constant but different near the origin; hence both local slopes vanish and only source value/intercept is separated by this construction. If the observer were forced to comove with the modified source value, the exterior normalization would change and this proof would no longer establish equality.

Under identical complete data laws, simultaneous inclusion of the two parameter points has probability at least `1-2α` by the union bound. On that event the diameter is at least their separation. The point-estimation lower bound follows from the triangle inequality under that same common law. Neither bound assumes independent coverage events, and neither is a numeric uncertainty statement for an actual catalogue.

## 4. Stronger readings and remaining decisions

| Stronger reading | Decision | Reason |
|---|---|---|
| Actual CF4/Union3 native law, full covariance, selection, calibration and source interpretation are validated. | HOLD | No corresponding data-contract audit or fit was performed. |
| The proposed confidence sets have useful practical width or power. | HOLD | Coverage alone does not establish either; no realistic power study or certified set computation was supplied. |
| A minimized nonlinear residual or likelihood ratio automatically follows a chi-square law with a parameter-count correction. | REJECT | N1's proof applies only at the true complete parameter after projection of fixed linear nuisances. |
| A failed local null optimizer or an empty total model constitutes acceleration detection. | REJECT | Neither supplies the required nonempty alternative and certified null exclusion. |
| Geodesicity exclusion always implies a strictly positive acceleration infimum. | REJECT | An admitted unbounded distance-scale orbit is a direct counterexample. |
| All scalar summaries fail, or all real surveys have identical laws after power compression. | REJECT | The repair scalar and the restricted Gaussian hypotheses disprove these broad readings. |
| The cutoff theorem proves an acceleration-identification floor or an Einstein-dust counterexample. | REJECT | Both origin slopes vanish; the fields are test congruences with a generally accelerated transition. |
| Equal data laws persist after adding arbitrary interior-sensitive observables. | REJECT | The observation-kernel restriction is essential. |
| This packet establishes a new general statistical principle, original priority, or publication readiness. | HOLD | Neyman inversion, Gaussian rotational invariance and two-point bounds are standard; the physical assembly needs a focused novelty and application audit. |

## 5. Closeout

The completed statistical result is a conditional native-observation confidence construction with careful nuisance/remainder treatment, plus explicit examples showing which information radial designs and separate angular powers can lose. The orientation-preserving scalar provides a positive diagnostic at the ideal coefficient level. These are analytically verified additions to the prior GR results, not observed evidence of source acceleration.

The 12-claim statistical gate is complete. Empirical probability-model closure, usable power, certified computation, fixed-matter extensions of the information examples, and publication novelty remain separate tasks. Additional operational-conformal or newly supplied project-source results may be reviewed in a separate addendum; they do not silently alter these 12 decisions or the preceding 18 GR decisions.
