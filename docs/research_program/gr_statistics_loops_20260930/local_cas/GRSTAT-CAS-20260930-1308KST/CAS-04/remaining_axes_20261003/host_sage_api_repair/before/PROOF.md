# CAS-04 Sage/Singular axis: partial execution

The frozen `EXECUTION_CONTRACT.json` is SHA-256
`058da4a8716fd06bc67100b8490df88a6783b780ac0ff66bf1221a02ab7e8741`;
`COMMON_SPEC.md` is SHA-256
`4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`.
This axis used only those mathematical inputs. The current axis result is
**INCONCLUSIVE**: Sage's exact component calculations ran successfully, but
the required Singular saturation certificate did not pass. No mathematical
counterexample was found.

## Algebra and domains

Use a rest orthonormal frame with `u=(1,0,0,0)`, signature `(-,+,+,+)`,
physical `U=c u` with `c>0`, mixed `T=diag(-epsilon,p1,p2,p3)`, and signed
gaps `g_i=epsilon+p_i`. Assume a smooth normalized selected eigenline and
each `g_i != 0`; for the bound also assume `delta=min_i |g_i|>0`.
All squares and Frobenius norms below are positive Euclidean component norms.
The rational-function calculations are over `QQ` and are valid only on these
nonzero-denominator domains. The future/eigenline and differentiability
conditions are analytic hypotheses, not consequences of these calculations.

**C01.** Differentiate `T u=-epsilon u` along arbitrary `X`:
`(nabla_X T)u+(T+epsilon I)nabla_X u=-(X epsilon)u`.
Normalization gives `g(u,nabla_X u)=0`; spatial projection kills the final
term. On the rest space, `L=S_T+epsilon I` has eigenvalues `g_i`, hence
`L nabla_X U=-c h(nabla_X T)u`. With
`D_{mu i}=[h(nabla_mu T)u]_i`, the four rows of the derivative are
`Q_{mu i}=nabla_mu U_i=-c D_{mu i}/g_i` and `Q_{mu 0}=0`.
Sage inverted the diagonal `L` and checked all four row equations exactly.

**C02.** Write `M_ij=Q_ij`, `theta=tr M`,
`sigma=(M+M^T)/2-(theta/3)I`, and `W=(M-M^T)/2`.
Then `M=(theta/3)I+sigma+W` is an orthogonal decomposition in the
Euclidean Frobenius inner product; `sigma` is tracefree and symmetric and
`W` is skew. In the derivative-first convention,
`(omega_1,omega_2,omega_3)=(W_23,-W_13,W_12)`, so
`||W||_F^2=2|omega|^2`, `W x=-omega cross x`, and this `W` is
`-c` times the stated book vorticity. Since `A_i=c Q_0i`, the time row
contributes `|A|^2/c^2`. Sage checked the reconstruction, symmetry,
trace, skew norm, and exact 4-by-3 identity

`theta^2/3+||sigma||_F^2+2|omega|^2+|A|^2/c^2
 = c^2 sum_{mu=0..3,i=1..3} D_{mu i}^2/g_i^2`.

**C03.** Sage checked the exact rational identity

`c^2 ||D||^2/delta^2 - c^2 sum D_{mu i}^2/g_i^2
 = c^2 sum D_{mu i}^2 (g_i^2-delta^2)/(delta^2 g_i^2)`.

Every right-hand summand is nonnegative because `c>0`, `delta>0`,
`g_i^2>=delta^2`, and the norms are positive component norms. Thus the
requested upper bound holds for either sign of every `g_i`. The sum vanishes
iff `D_{mu i}=0` for every index with `|g_i|>delta`; components supported
in minimal absolute-gap eigenspaces can remain. For a perfect-fluid rest
tensor all three gaps coincide, so the bound is saturated whenever the
component identity applies. No indefinite Lorentz norm enters this argument.

**C04.** At the rest event, expand
`T^{ab}=(epsilon+p)u^a u^b+p g^{ab}` and its divergence, with
`partial_mu u^0=0` from normalization. The spatial projection is exactly
`(epsilon+p) partial_0 u^i+partial_i p`.
Conservation and `epsilon+p != 0` give
`A_i=c^2 partial_0 u^i=-c^2 D_i p/(epsilon+p)`.
For a differentiable barotropic EOS with
`c_s^2=c^2 dp/d epsilon`, the chain rule gives
`A_i=-c_s^2 D_i epsilon/(epsilon+p)`. If `p=0` as a dust field,
then `Dp=0`; positive `epsilon` supplies the nonzero denominator and `A=0`.
A bound on `c_s^2` alone cannot bound acceleration without controlling the
density gradient and enthalpy gap. Sage checked the divergence expansion,
Euler algebra, barotropic substitution, and dust specialization exactly.

## Engine execution and failed attempt

`run.py` imposed a separate 1800-second hard timeout on each engine and
recorded exact argv, cwd, exit, timestamps, raw logs, and SHA-256 of source
and logs in `AXIS_RESULT.json`. SageMath 10.9 and Singular version code 44100
were observed. Both engine subprocesses exited zero in both attempts.

The first Singular source omitted `LIB "elim.lib"`; Singular prints script
errors to stdout yet exits zero. The first runner accepted marker text despite
those errors and emitted a **false PASS**. Its complete source, envelope, and
logs are preserved in `attempt_01/` and are invalid as evidence.

One correction loaded `elim.lib` and required stdout to consist of exactly
three expected markers. The retry's Singular output was
`SAT_EQUAL=0`, `INVERSE_PRODUCT=1`, and `TWELVE_ROW_RESIDUALS=0`;
the complete retry source, envelope, and logs are preserved in `attempt_02/`.
Inspection of installed `elim.lib` shows `sat(id,j)` returns an ideal directly,
while `sat_with_exp(id,j)` returns a list. The retry source used
`sat(J,ideal(G))[1]`, selecting one generator of the saturated ideal. This
explains the two zero markers. The allowed one correction and retry were
exhausted, so that source was not changed or executed again. The current
`AXIS_RESULT.json` correctly reports `INCONCLUSIVE`; Singular saturation
remains unverified by this axis.

This work establishes neither smooth eigenfield existence/IFT nor a spectral
norm theorem, EF6 local existence, CAS-05/06 dependencies, or scientific
admission. No sibling-axis result or derivation was inspected.
