# CAS-04 independent SymPy finite-component proof

Inputs are the exact CAS-04 execution contract (SHA-256
`058da4a8716fd06bc67100b8490df88a6783b780ac0ff66bf1221a02ab7e8741`)
and neutral `COMMON_SPEC.md` (SHA-256
`4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`).
The script uses no sibling derivation or result. It checks finite algebra at a
point in an orthonormal rest frame with signature `(-,+,+,+)` and `U=c u`,
`c>0`. Smooth existence of the eigenfield is an input, not established here.
All gaps `g_i=epsilon+p_i` are real and nonzero and
`delta=min_i |g_i|>0`; signed gaps are allowed. Norms below are positive
Euclidean rest-component norms.

## C01: differentiated eigenvector and spectral solution

Covariantly differentiate `T u=-epsilon u` along any `X`:

`(nabla_X T)u+(T+epsilon I)nabla_X u=-(X epsilon)u`.

Since `g(u,u)=-1`, `nabla_X u` is spatial. Applying the mixed rest projector
`h^a_b` kills the right side. On the rest space, `T+epsilon I` is
`L=S_T+epsilon I`; thus `L nabla_X U=-c h(nabla_X T)u`.
For each of four derivative directions the script forms the three projected
equations with independent unknown spatial derivatives, solves the resulting
12-variable diagonal linear system, and verifies its unique solution
`Q_{mu i}=nabla_mu U_i=-c D_{mu i}/g_i`. The rank/inversion claim uses the
declared nonzero gaps. The timelike derivative component vanishes from unit
normalization; no derivative of `epsilon` is set to zero.

## C02: full 4 by 3 decomposition

Let `M_ij=Q_ij`, `theta=tr M`,
`sigma=(M+M^T)/2-(theta/3)I`, and `W=(M-M^T)/2`.
Then `M=(theta/3)I+sigma+W` is an orthogonal decomposition for the
Frobenius inner product: `sigma` is symmetric tracefree, `W` is skew,
and cross terms vanish. With `W_ij=epsilon_ijk omega_k`,
`||W||_F^2=2|omega|^2` and `W x=-omega cross x`; the script checks the
sign explicitly. The acceleration convention gives `A_i=c Q_{0i}`. Hence

`theta^2/3+||sigma||_F^2+2|omega|^2+|A|^2/c^2`
`=sum_{mu=0}^3 sum_{i=1}^3 Q_{mu i}^2`
`=c^2 sum_{mu,i} D_{mu i}^2/g_i^2`.

The script certifies both exact residuals as zero for twelve independent
real `D` symbols, rather than selecting a numerical derivative array.

## C03: universal finite bound and equality support

For every real, nonzero `g_i` with `|g_i|>=delta>0`, the script verifies
the following exact rational identity for independent `D_{mu i}`:

`c^2||D||^2/delta^2 - c^2 sum D_{mu i}^2/g_i^2`
`= c^2 sum_{mu,i} D_{mu i}^2 (g_i^2-delta^2)/(delta^2 g_i^2)`.

Each summand is nonnegative by the declared domain. Consequently the
left side is nonnegative for every finite 4 by 3 array. It vanishes exactly
when `D_{mu i}=0` for each column with `|g_i|>delta`; columns with
`|g_i|=delta` may have arbitrary support. This is the equality-support
condition. All perfect-fluid gaps equal `epsilon+p`, so they saturate the
bound when their nonzero enthalpy is the minimal gap. A signed-gap check
uses `(-2,3,-4)`, `delta=2`; support only in the first column yields zero
deficit, and adding one unit to the second column yields exact deficit
`5/4` with `c=3`. The numerical instance is ancillary to the general SOS
identity and sign proof.

## C04: projected conserved-fluid Euler equation

Write `T^{ab}=(epsilon+p)u^a u^b+p g^{ab}`. Product-rule divergence and
spatial projection of `nabla_a T^{ab}=0` give
`(epsilon+p)u^a nabla_a u^b+D^b p=0`.
The script builds the full product-rule divergence using independent
derivative symbols and checks in the rest frame that its three spatial
components are exactly `(epsilon+p)v_{0i}+partial_i p`. Solving those
equations, and using `A^b=nabla_U U^b=c^2 u^a nabla_a u^b`, yields
`A=-c^2 Dp/(epsilon+p)`. For differentiable barotropic `p(epsilon)` and
`cs^2=c^2 dp/depsilon`, substitution gives
`A=-cs^2 D epsilon/(epsilon+p)`. These equations require the nonzero
enthalpy gap. If `p=0` identically and `epsilon>0`, then `Dp=0` and `A=0`.
A sound-speed bound alone does not bound `A` without a density-gradient or
enthalpy control: scale `D epsilon` while holding `cs^2` and enthalpy fixed.

The first local run exited 1 because the C02 checker placed a matrix object
inside a scalar-zero list. That was a checker construction error; the
matrix entries and independent C01 unknowns were corrected before the
captured final run. Final `RUN_EXECUTION.json` binds source, contract,
common specification, argv, cwd, process exit and raw stdout/stderr.
The four finite components are the entire axis scope. Eigenfield
existence/IFT, spectral-norm extension, EF6 analytic dependencies through
CAS-05/06, and scientific admission remain unproved by this axis.
