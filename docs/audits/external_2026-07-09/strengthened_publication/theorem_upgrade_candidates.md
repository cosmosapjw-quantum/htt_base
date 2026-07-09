# 추가로 증명 가능한 정리 후보들

아래 정리들은 “claim을 낮추는” 게 아니라, 심사위원이 공격한 지점을 더 강한 수학 명제로 바꾸는 후보들이다.

## T1. Constraint-derived uniqueness of the signed comparator

**Statement.** Fix signature (-,+,+,+), congruence n^a, H=Θ/3, and registered dimensionless components

\[
\Sigma^2=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},\quad
W^2=\frac{\omega_{ab}\omega^{ab}}{6H^2},\quad
\Omega_{\rm tilt}=(1+w)\Omega_m\sinh^2\beta,
\]

with curvature component \(\Omega_{k,\rm aniso}=\Omega_k-\Omega_{k,\rm ref}\). Among linear dimensionless comparators that read off the non-FLRW contribution to the Gauss constraint while assigning zero to the FLRW reference branch, the coefficient vector is uniquely

\[
c=(1,-1,1,1).
\]

**Proof route.** Divide the 1+3 Gauss constraint by \(3H^2\), match normalized shear/vorticity terms, introduce tilted-frame energy excess, and subtract the registered FLRW reference. Uniqueness follows because the four registered components form an independent coordinate basis in the comparator layer.

**Potential obstruction.** If \(\Omega_{k,\rm aniso}\) is allowed to be signed, the “component magnitude cone” must be replaced by a signed affine coordinate. The theorem must explicitly choose one convention.

## T2. Local constrained-data sharpness theorem for P31

**Statement.** Let \(g\) be sufficiently small in the registered HTT component cone and let the branch specify an equation of state and energy-condition domain. Under nondegeneracy of the York/conformal constraint operator, each endpoint of the P26 identified interval is realized by a local CMC initial-data family whose first-jet invariants match the endpoint components up to controlled \(O(\|g\|^2)\) residual; after conformal correction the Hamiltonian and momentum residuals vanish to solver tolerance.

**Proof route.** Start with local nearly-FLRW initial data, add transverse-traceless shear, stream-realized tilt stress, and small anisotropic curvature perturbations. Check first-order constraints. Apply implicit-function/conformal method to correct residuals. Use continuous dependence to preserve the comparator endpoint value up to controlled error.

**Numerical witness.** Implement `constraint_realization_endpoint_solver.py`: sweep eps, solve correction, report residual norms and convergence slopes.

**Why this strengthens the paper.** It turns “sharp over an abstract cone” into “sharp over an explicit physically realizable local-data class.”

## T3. Exact equality conditions for P36 joint depth-gap intervals

**Statement.** Let \(S\) be a compact polytope and \(N(s)=n+c_N\cdot s\), \(D(s)=d+c_D\cdot s>0\). The joint feasible interval for \(G_F=N/D\) is the exact image of the diagonal feasible set and is always contained in the marginal quotient interval. Equality of the lower endpoint holds iff the numerator-minimizing feasible face and denominator-maximizing feasible face contain a common point satisfying the linear-fractional lower optimum. Equality of the upper endpoint holds iff the numerator-maximizing feasible face and denominator-minimizing feasible face contain a common point satisfying the upper optimum. Outside these compatibility conditions, inclusion is strict. For generic coefficient vectors, equality conditions define a lower-dimensional algebraic/face-incidence set.

**Proof route.** Use Charnes-Cooper transform or quasiconvex/quasiconcave linear-fractional optimization on polytopes. Marginal quotient optimizes over \(S\times S\), joint over diagonal \(\Delta(S)\). Strictness reduces to whether product-space extremizers intersect the diagonal.

**Numerical witness.** Included in `scripts/strengthening_core.py`; strictness is generic in random coefficient draws, while the critique equality case is reproduced exactly.

## T4. Known-covariance two-stage identified-set coverage

**Statement.** Under Gaussian whitened noise with fixed response matrix R, the residual projection statistic is \(\chi^2_{m-r}\) and independent of the reachable projection. Stage-1 EMPTY controls specification-test false rejection at \(\alpha_1\). Conditional stage-2 ellipsoid covers the reachable projection at \(1-\alpha_2\). For scalar \(x_C\) inside an interval-identified set, Imbens-Manski critical values give pointwise parameter coverage; two-sided endpoint/projection intervals give simultaneous identified-set coverage.

**Proof route.** Orthogonal projection of Gaussian vector into column space and residual space; then standard partial-identification endpoint logic.

**Numerical witness.** Included: residual EMPTY rate at zero shift is 0.04868 for \(\alpha_1=0.05\); power rises with residual shifts.

## T5. Estimated-covariance robust endpoint coverage

**Statement.** If covariance is estimated from \(N_{\rm sim}\) Gaussian simulations, the inverse sample covariance is biased. Using uncorrected Gaussian plug-in precision inflates reachable-sector precision. Hartlap correction removes first-order precision bias; Sellentin-Heavens covariance marginalization replaces the Gaussian likelihood by a multivariate-t form and propagates covariance uncertainty. Endpoint intervals must condition on this policy.

**Proof route.** Wishart expectation of inverse covariance; compare plug-in, Hartlap-corrected, and covariance-marginalized likelihood.

**Numerical witness.** Included: for p=20, raw precision trace ratio is ~1.075 at Nsim=300 and ~1.036 at Nsim=600; Hartlap-corrected mean is ~1.

## T6. Prior-exposure decomposition theorem

**Statement.** If likelihood depends on g only through Rg and column j of R is zero, then an independent prior leaves the posterior marginal of \(g_j\) equal to the prior exactly. If prior couples \(g_j\) to reachable coordinates, posterior movement of \(g_j\) is mediated entirely by the prior coupling and must be labelled prior-exposed.

**Proof route.** Factorization of posterior density; KL divergence of identical prior/posterior marginal is zero.

**Numerical witness.** Included in response-rank/prior exposure script.

## T7. Finite-cover dependent e-value merger theorem for K1/K5 scans

**Statement.** For e-values \(E_k\) satisfying \(E_0 E_k\le 1\) under a common null, any convex weighted average is an e-value under arbitrary dependence. If sequential e-values satisfy \(E_0[E_t\mid\mathcal F_{t-1}]\le 1\), the product process is a nonnegative supermartingale and Ville control is anytime-valid.

**Proof route.** Linearity of expectation for finite cover; supermartingale property and Ville inequality.

**Numerical witness.** Included: dependent average e-value mean is ~0.997 and 200-step Ville crossing is 0.0397 for β=0.05.

## T8. Scalar/BiPoSH non-equivalence theorem

**Statement.** Diagonal \(C_\ell\)-style compression annihilates off-diagonal \(L>0\) covariance morphology. Therefore scalar low-ell statistics and BiPoSH covariance statistics are non-equivalent projections; agreement or disagreement between them is a diagnostic pattern, not a geometry label.

**Proof route.** Schur orthogonality and rotational decomposition of covariance into BiPoSH coefficients.

**Data witness.** K1 map-stability matrix must report scalar and BiPoSH channels side by side with separate nulls.

## T9. Transverse/spin-2 reopening theorem

**Statement.** Radial contractions annihilate antisymmetric vorticity contributions, but transverse velocity and spin-2 response tensors need not. Adding such channels can increase response rank and reopen sectors that are structural nulls for scalar/radial channels.

**Proof route.** Tensor symmetry: \(n^a\Omega_{ab}n^b=0\), while screen-space and spin-2 tensors are not equivalent to the radial dyad.

**Numerical witness.** Toy rank certificates: scalar/radial rank 2, enlarged transverse/spin-2 rank 4.

