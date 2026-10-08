# Conditional analytic synthesis for a supplied Jacobi system and C² scalar

**FORMALLY_CHECKED; separate independent review SCOPED VALID.** Owner: htt; transfer source: none; scientific admission: HOLD. This successor uses a new strength-based validation plan; it is not a new CAS_4AXIS_PASS or a historical campaign adjudication.

Let E=ℝ² with its standard Euclidean inner product and induced operator norm. K≥0, L>0, c>0, M₂≥0. The supplied operators D,D₁,D₂,R obey exactly `CAS07M05.JacobiPremises K L`: within-interval derivative witnesses D'=D₁ and D₁'=D₂ on [0,L], continuous D₂ and R, D(0)=0, D₁(0)=Id, D₂(r)=−R(r)∘D(r), and ‖R(r)‖≤K throughout [0,L]. The supplied scalar witnesses Z,Z₁,Z₂ obey exactly `ScalarPremises L M2`: HasDerivAt Z (Z₁ r) r and HasDerivAt Z₁ (Z₂ r) r at every r∈[0,L], continuous Z₂ there, and |Z₂(r)|≤M₂ throughout that interval. These endpoint assumptions deliberately match M02 rather than silently weakening it. Set Z₀=Z(0), H₀=c Z₁(0), with arbitrary absolute Z₀.

Define f_K(r)=r at K=0 and sinh(√K r)/√K for K>0; for r>0 define η(r)=f_K(r)/r−1. Assume only the small-distortion input η_L=η(L)<1 in addition to the preceding system/scalar inputs. For every 0<s≤L set d_A=√det(matrixOf(D(s))) on the positive root branch and t=min(L,d_A/(1−η_L)). The compiled theorem gives simultaneously:

- ‖D(s)‖≤f_K(s), ‖D(s)−s Id‖≤f_K(s)−s, and the identical coordinate-matrix operator norm bound ≤sη(s).
- det D(s)>0 and [s(1−η(s))]²≤det D(s)≤[s(1+η(s))]².
- d_A>0 and s(1−η(s))≤d_A≤s(1+η(s)); both 1−η(s) and 1−η_L are positive.
- |Z(s)−Z₀−H₀s/c|≤M₂s²/2, derived from M02.
- FD1: |Z(s)−Z₀−H₀d_A/c|≤M₂s²/2+|H₀|sη(s)/c.
- FD2: the same left side ≤M₂d_A²/[2(1−η_L)²]+|H₀|d_Aη_L/[c(1−η_L)].
- FD3: |c(Z(s)−Z₀)/d_A−H₀|≤cM₂s/[2(1−η(s))]+|H₀|η(s)/(1−η(s)).
- 0<s≤t≤L and 0≤η(s)≤η(t)≤η_L<1.
- The FD1 left side ≤M₂t²/2+|H₀|tη(t)/c, and that refined right side is no greater than the FD2 right side.

The original C03 and M06 ADMITTED_INPUTS.json formulas were read and matched term by term, including c, absolute H₀, factor 2, and the two denominator powers. `algebra_premises` derives C03's Taylor and screen fields; no FD conclusion is assumed. M04 obtains whole-interval norm estimates through M03. M05 supplies the finite-dimensional coordinate isometry and general nonsymmetric C02 determinant bridge. Neither D symmetry nor D/R commutation is assumed. The additional squared determinant bounds are derived with the positive-root identity and nonnegative endpoints in the new kernel proof.

| Conclusion / new obligation | Exact source theorem | Evidence scope |
|---|---|---|
| Jacobi norm estimates | M04 `Cas07M04.d_norm`, `d_minus_si` | Reused accepted kernel interfaces |
| Finite-dimensional conversion and matrix error | M05 `matrixOf`, `opnorm_error_eq`, `c02_premise` | Reused accepted kernel interface |
| Determinant sign and distance | M05 `determinant_distance_bridge`, importing C02 `CAS_07_C02_full` | Reused accepted kernel interfaces |
| η order and positive denominators | M01 `eta_bounds`; M06 `eta_order` | Reused accepted interfaces and new linear implication |
| Scalar remainder | M02 `remainder_bound_physical` | Exact source minimally compiled as dependency, then applied |
| Derived C03 input, not target assumption | New `CAS07Synthesis.algebra_premises` | FORMALLY_CHECKED |
| All FD conclusions | C03 `FD1`, `FD2`, `FD3` | Reused accepted interface, applied to derived premises |
| t and comparison | M06 `t_domain`, `refined_fd1`, `no_worse_than_fd2` | Exact source minimally compiled as dependency, then applied |
| Squared determinant and universal conjunction | New `conditional_analytic_synthesis` | FORMALLY_CHECKED |
| s=0 and both min branches | New `closed_interval_controls`, `min_branches` | FORMALLY_CHECKED |

Boundary interpretation: at K=0, the accepted M05 `zero_curvature_control` and M06 `k_zero_control` give D(s)=s Id, det D(s)=s², d_A=s, η_L=0, t=s for 0<s≤L. H₀=0 and M₂=0 are allowed directly by the compiled universal theorem; specializing its formulas removes their corresponding nonnegative terms. With both zero the FD1 bound forces Z(s)=Z₀. These specializations are DERIVED from the compiled theorem, rather than separately executed full campaigns. At s=0 only the compiled closed-interval norm and Taylor conclusions are used; no division by s or d_A is asserted. Both min branches include equality. As η_L→1⁻ denominator positivity holds at each admitted parameter; no uniform finite bound in that limit is claimed, and η_L=1 remains excluded. This is Euclidean positive norm reasoning; it does not use a Lorentz norm. The surrounding signature convention remains (−,+,+,+).

Actual new execution: `python …/conditional_synthesis_v1_20261008/build.py`, with exact argv/cwd/environment subset and source SHA-256 in `logs/20261008T104259728756Z/execution.json`. Version, M02 dependency, M06 dependency and synthesis each exited 0. Lean is 4.31.0, mathlib is `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. All four new theorem axiom reports are exactly `[propext, Classical.choice, Quot.sound]`; no sorryAx or target axiom. Existing six accepted `.olean` digests matched the published dependency pins before execution. M02 and M06 compilation is part of the new build, not retrospective campaign revalidation. Wolfram/SymPy/Sage were not invoked: new inequalities and branch handling were proved in Lean, with no numerical universalization. No numerical-output implementation path changed.

Independent review: `review/REVIEW.md` reports SCOPED VALID with no blocking findings for synthesis source `39bf9debfd249e274a9c840f1c096a1bad692e605ff6c9286c284821e0d5f770`. Requested and observed reviewer gpt-6-astra / ultra, fresh context, production read-only. The reviewer inspected target/dependencies and independently reasoned first, then audited proof/logs and rebuilt M02, M06, Synthesis and ReviewChecks; all exits 0 and synthesis axioms standard-only. Exact command/version/source/runtime evidence is preserved under review/. Existing component evidence remains reused, not independently rediscovered by the new authors.

UNRESOLVED / outside this conditional theorem: C01, physical ray/source-field existence, whole-interval construction/uniqueness, native Bianchi result, catalogue eligibility and statistical coverage. Historical contracts, reviews and adjudications remain unchanged; scientific admission HOLD. New author compilation and new reviewer compilation are distinct evidence stages.
