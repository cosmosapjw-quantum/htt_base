# Independent scientific review of the expanded HTT analysis

Review date: 2026-10-24. Scope: one bounded R6 pass on the new local optical bridge, its relation to the retained contraction theorem, the two-radius design, and the recovered frame correction; one requested follow-up on the orientation inverse. Reviewer did not author these results, imported no author calculation functions, changed no manuscript/source data, ran no solver/ODE, made no Git mutation, and created no child reviewer. Requested runtime: `gpt-6-astra`, `xhigh`; observed runtime metadata: `UNKNOWN`.

`skill_context_used`: PhysMath Research Loop 1.3.0 (`c38/physmath-research-loop/SKILL.md`), `references/POLICY_INTEGRATION.md`, `references/THEORY_LOOP.md` (R6), and `references/SUBAGENT_MODE.md`; the bounded parent packet and source `AGENTS.md` scientific assumptions were retained. This is a scientific derivation/check, not a novelty or final manuscript-readiness verdict.

## Findings requiring the smallest manuscript repair

1. **State directional positivity before T3–T4.** `H>0` alone does not make the exact full-sphere logarithm or the positive-redshift local inverse well defined. For example, `S=0`, `d=2 e_z` gives `1+q=-1` at the south pole. Require `1+q(n)>0` on the full sphere before introducing T3. For the smooth finite multipole field, strict full-sphere positivity supplies a positive minimum. The later `sup|q|≤ε<1` is sufficient and gives the stronger expansion domain for T7–T13. A restricted angular domain would require a different moment inverse. This is a claim-domain omission, not a failure of the tensor construction. Parent acknowledged the repair; final integrated prose was not yet supplied to this reviewer.

2. **Replace the unqualified small-shear conditioning sentence.** T13 correctly bounds absolute error by `E3/(κ s_min)`. As `S→0`, the absolute inverse gain diverges, but the relative condition number does not: for nonzero STF `S`, `λ_max²≤2(S:S)/3`, so `κ₂(L_S)≤sqrt(9/5)`. Say that reconstruction becomes increasingly sensitive to fixed absolute octupole errors. Parent acknowledged this wording repair. No change to T10–T13 is needed.

3. **Preserve the explicit curvature/congruence correction to baseline equation (15).** The baseline's qualification by an unspecified closure is insufficient to decide which vorticity sign accompanies its curvature. The recovered `mathematical_recovery.md` now gives the necessary branch distinction correctly. In its declared `c=1` convention,
   `R_rest=R_proj−θ²+V_ab V^ba` and `R_same=R_rest+2ω_abω^ab` imply
   `Ωk_same=Ωk_rest−2W²`.
   The Einstein-normalized rest-bundle constraint contains `Σ²−W²+Ωk_rest`; the same-order scalar contains `Σ²+W²+Ωk_same`. A switch of curvature scalar cannot preserve the old vorticity sign. This is already repaired in the inspected recovery block; retain that block in the final integration. On a hypersurface normal, the independent restriction is `W[n]=0`.

No other material algebraic or numerical defect was found in the reviewed bridge/design. The finite checks below support the stated identities and bounds; their general validity follows from the derivations, not from the count of passing cases.

## Independent derivation and conventions

For dimensionless unit timelike `u`, proper length `s=cτ`, physical acceleration `A` has units length/time² and physical rates `H,σ,ω` have units 1/time. Therefore `∇u=−u⊗A/c²+(Hh+σ+ω)/c` has units 1/length. With the specified observer-to-source direction and `ℓ=−u+n`, `u·ℓ=1`, giving `c ℓℓ:∇u=H−A·n/c+σ:nn`. The antisymmetric term vanishes. The sign in T1 is correct; reversing the source-direction convention would reverse the acceleration term. With common emitter/observer congruence, photon/geometric-optics assumptions and local invertibility, `dL=cz/H_u+O(z²)` yields T3 under the positivity condition above. This has inverse-time `H_u` and length `dL`, with dimensionless logarithm and magnitude-valued `fμ,Oμ`.

Primary-source checks were made directly against [Heinesen 2021, equations (26), (29), section 5](https://arxiv.org/html/2010.06534v2) and [Maartens et al. 2024, equations (15), (24), (28), section 4.2](https://arxiv.org/html/2312.09875v3). Heinesen's negative acceleration dipole and local distance coefficient agree. Maartens' distinct boosted-distance octupole issue does not refute the same-congruence logarithmic calculation here. The dust specialization in Maartens has zero acceleration; the accelerated general congruence is supported by Heinesen. This source check does not identify optical tensors with CMB tensors.

For the cubic polynomial `P(x)=(d·x)(xᵀSx)`, trace freedom gives `ΔP=4(Sd)·x`. Since `Δ[|x|² b·x]=10 b·x`, its harmonic part is `P−(2/5)|x|²(Sd)·x`. Restriction to the unit sphere independently gives T6 and its rank-three STF coefficients. The quadratic logarithm term is `+κq²/2`; only its odd cross term has degree three. Its coefficient is therefore `+κL_Sd`, confirming T7, including sign and the absence of a factor two.

For any STF cubic `O`, trace terms drop out of `(L_Sd):O`, and symmetry makes its three product terms equal. Hence `L_S*O=O:S`. Contracting the harmonic tensor with `S` gives `L_S*L_S=(S:S)I/3+(2/5)S²=K_S`; this proves both the norm identity and the positive inverse on every nonzero `S`, including repeated shear eigenvalues. The decomposition in T12 is precisely the orthogonal projection onto `im L_S`; its residual has dimension four and annihilates contraction with `S`. This is consistent with the retained theorem's notation, where the contraction rather than the lift was called `L_Q`. No transpose or scaling mismatch was found.

For a harmonic cubic, the normalized spherical squared norm is `(2/35)||O||F²`. The scalar uniform log remainder `κ ε³/[3(1−ε)]`, the contraction property of the angular projector, and this norm conversion yield T8. For pure dipole, only odd powers contribute to degree three; removing the cubic leaves a scalar odd tail bounded by `κ|d|⁵/[5(1−|d|²)]`, yielding T9. Projecting the remainder and applying the lift pseudoinverse yields both T13 inequalities. These arguments do not control finite-redshift, calibration or observer errors, consistently with the draft's stated scope.

For an arbitrary constant intercept `C`, exponentiation gives `exp[−(fμ+C)/κ]=exp(−C/κ)(1+q)`. The full-sphere mean is `exp(−C/κ)` since both dipole and STF quadrupole average to zero. Second/fourth sphere moments give `3<rn>=d` and `(15/2)<r(nn−I/3)>=S`. Thus T4 is exact for the complete ideal field, including the unknown intercept. The distinction from exponentiating an incomplete/noisy harmonic fit is necessary and already stated.

Writing `b=κK_Sd`, commutation of `K_S` with `S` gives `[b,Sb,S²b]=κK_S[d,Sd,S²d]`, and thus T13a. Since `K_S` is positive definite for nonzero `S`, its determinant preserves the sign. A repeated spectrum or missing eigenframe component yields zero, as stated. This is a leading optical-response relation for a specified shear, not an unqualified sign certificate for the full logarithm. For the actual magnitude quadrupole, `Qμ=−κS+O(t²)` at common small amplitude; `χ(aQ,bO)=a⁶b³χ(Q,O)` explains why the quadrupole's minus sign does not reverse the leading chirality. The full response still needs a nonzero margin against its remainder before asserting sign stability.

## Executed independent checks

Command: `python HTT_EXPANDED_20261024/research/independent_review_check.py` from `/workspace/scratch/ef61c9590364`; final exit **0**. The initial optional-SymPy version could not run in either default or primary Python because SymPy was absent. It was replaced by exact `Fraction` polynomial arithmetic; no package was installed. The final script needs only Python and NumPy and writes no results or figures.

The independent projector uses seven harmonic cubic polynomials, their directly evaluated full-sphere Gram matrix, and least squares, rather than the author's STF moment projector. A polynomial Laplacian constructs the exact harmonic cubic. Nine exact rational cases use full non-diagonal shear matrices. The floating tests use 24 generic states with sufficient uniform bounds from 0.01 to 0.71, a 48-by-96 angular grid, arbitrary STF octupoles for the adjoint check, and a nonzero intercept. These checks do not import author functions.

| Check | Observed maximum or result |
|---|---:|
| Exact harmonic trace, norm, contraction and chirality factorization | 9/9 exact rational cases |
| `||L*L−K_S||F` | `3.9351e−15` |
| Adjoint residual | `6.3564e−14` |
| Intercept-free `(d,S)` reconstruction error | `3.5066e−14` |
| Projected residual contraction `||O_perp:S||` | `8.0789e−17` |
| Exact-log remainder / T8 envelope | `0.058146` |
| Residual projection / T8 envelope | `0.024833` |
| Reconstruction error / T13 envelope | `0.043285` |
| Pure-dipole remainder / T9 envelope, `|d|∈{.05,.2,.5,.8}` | `0.167851` |
| Stored author two-grid maximum difference | `1.2046551275404449e−14` |

The stored 45-row bridge JSON also satisfies every recorded T8 bound. Its grid comparison agrees with the draft's conservative `1.21e−14` display. The author's cubic-dipole bound was not originally an asserted numerical check in its script; the independent test supplies a targeted check of that formula without changing the author artifacts.

## Rank-thirteen example and recovered physical scope

The rank proof in `mathematical_recovery.md` is correct. The nine first-shell equations give `h=−(c/R1)La`; the four repeated directions give `(1−R2/R1)E4 a=0`. The stated invertibility assumptions then force a zero kernel. With the same unisolvent directions and equal radii, rank is exactly nine, not thirteen.

Independently recomputed exact values are `det E9=331776/15625`, `det E4=−2`. The normalized 13-by-13 determinant is `−(663552/15625)(1−r)^4`. Because only four rows depend linearly on `r`, its degree is at most four; exact evaluation at five distinct rational radii verifies the complete determinant polynomial. Restoring units gives `R1⁵(R1−R2)⁴ det(E9)det(E4)/c⁹`, as in the recovery text. The two recorded condition numbers were reproduced: `1,634,438.3441892061` at radius separation `10⁻⁵` and `30.16385392447046` at separation one. These numbers are properties of the stated raw polynomial coordinates, with `R1=c=1`; they are not coordinate-invariant information measures or real-catalogue precision claims. The figure and recovery text correctly keep that scope.

The R190 frozen targets and addendum fix the comparator on a slice normal. Independently, `n=−N dt` implies the projected antisymmetric derivative vanishes for symmetric Hessian and torsion-free connection, so `W[n]=0`. The registered `[.11,.17]` factorized box consequently has constraint image `[.15,.17]` only in its stated Bianchi-I/V instantaneous construction. The lower endpoint `.11` is excluded, while `.17` has an instantaneous witness. This does not prove a local/global dynamical development. The original pair-density normalization defect and owner-defined frame issue are not repaired by silently relabeling that interval. The new recovery text respects these boundaries.

The inspected `physical_synthesis.md` retains the distinction between tensor morphology and Bianchi structure. Its flat/open isotropic example with matching instantaneous `H`, zero shear and zero vorticity demonstrates a degeneracy of those specified local observables; it does not claim degeneracy after adding curvature/history observables. Its family-image compatibility construction and common rotation of all blocks are mathematically appropriate within the given response assumptions. No new overclaim was found in that bounded check; the numerical observational/template claims in that file were outside this assignment.

## Requested orientation-inverse follow-up

For `Ahat W=[Mhat,W]`, simple spectrum makes the map from skew matrices injective. In Frobenius norms, `||Ahat W||²=2∑_{i<j}(λhat_i−λhat_j)² W_ij²` and `||W||²=2∑_{i<j}W_ij²`, so the least singular value is the minimum gap. The global least-squares solution obeys `What−W=Ahat†(Rhat−Ahat W)`. This gives the error constant **one**, with numerator `εR+2εM W*`; an additional factor two would be unnecessary. Weyl's ordered-eigenvalue bound gives `δhat≥δ−2εM`. Twenty independent rotated numerical cases satisfy the claimed bound, with maximum ratio `0.517230`. The text's distinction between a tensor response and a physical time derivative is appropriate.

## Completion boundary

The reviewed formulas and constructive inverse are supported under their stated and repaired domains. The parent owns final manuscript edits, incorporation of findings 1–2, preservation of the recovered frame branch, and artifact delivery. This report supplies one independent scientific pass and a reproducible targeted check script; it does not certify uninspected observational claims or novelty.

