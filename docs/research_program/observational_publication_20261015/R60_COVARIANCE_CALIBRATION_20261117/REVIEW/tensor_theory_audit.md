# Tensor likelihood and calibration sensitivity: independent mathematical report

## Scope and review identity

Author/reviewer role: independent child `/root/tensor_theory_audit`. Base and directly observed checkout HEAD: `6fe19c5139004a1f281ec85c592e5ab4c7590d5f`, branch `research/r58-mixed-tensor-convergence-20261117`. The authorized device and repository were read only. This report and its finite checks are scratch integration inputs; no repository change was made by this reviewer.

Primary verdict for the proposed physical-calibration confidence construction: **conditional on the named fixed-Gaussian data law, correct physical response, and declared calibration body**. The algebraic support and constrained-distance statements below are derived. Their finite implementations were independently checked against constrained optimization. No new universal no-go or cosmological detection is claimed.

Directly read: the complete R58 `fit_linear`, likelihood evaluator and interval/union functions; R54 five-view definitions, STF basis, support and gauge functions; R54 `THEOREMS.md` T1–T6 setting (first 155 lines); R58 `REPORT_KO.md`; R58 `THEORY_LOOPS.md` shared experiment and L1–L3 plus complete section index; original `cf4_growth_covariance.py` amplitude estimator and callers; `htt_five_variable_state.py` definitions and functional index; `typefree_functionals.py` definitions and index. Prior R58 mathematical review was read as historical evidence, not treated as a substitute for checking the new constructions.

Source byte identities at the observed HEAD:

| Source | SHA-256 |
|---|---|
| `htt/htt/htt/infer/r58_mixed_tensor_likelihood.py` | `f1c07d8ba7253f225af9354277a2973b5cab96c86febd08d4f8c5e1a11555bc0` |
| `htt/htt/htt/infer/r54_tensor_five_view.py` | `47f9ab5fd40da9ffb8725ff9720a8d4cba7116c905a6a4c11e05b79f972e17a8` |
| `htt/obsstat/cf4_growth_covariance.py` | `9ca870777cec9aaae262ac052196e92a37bf45fd522897fc86bbaa10080b79a6` |
| `htt/src/common/htt_five_variable_state.py` | `28742f297b5d754d98c9a97e70ae49acb70b9806b17b13c29bd178e0805c1778` |

## 1. What the tensor five-variable framework preserves

For one fixed experiment, write

\[
y\sim N(X\alpha,C),\quad J=X^TC^{-1}X,\quad t=X^TC^{-1}y,
\quad q_0=y^TC^{-1}y.
\]

When C and X are fixed independently of alpha, t is sufficient for alpha. The stored carrier `(J,t,q0,logdet C)` retains the normalized likelihood in that experiment. R58 also retains whitened X and y to avoid cancellation of the quadratic expression along poorly identified directions. This is a correct numerical refinement of the same likelihood.

If x retains the signed carrier, adding Q, Pi, F and G_F does not increase its statistical information. If x is replaced by its norm, amplitude, componentwise intervals or an insufficient scalar score, it can lose orientation, relative shape, cross-block dependence and physically estimable contrasts. Consequently the meaningful comparison is: exact/full Gaussian likelihood versus the tensor report (a tie), and both versus named lossy scalarizations (a potentially useful difference). It is too broad to say that the views can never improve a preexisting scalar analysis; they can restore information that that analysis discarded. The precise reference is the full-data or sufficient-statistic envelope.

The current 32-row compressed CF4 experiment is not shown sufficient for the raw 35,970-group catalogue. Equality to its 32-row full likelihood establishes equality only for that experiment. Varying a covariance amplitude makes fixed-C linear sufficient statistics insufficient for the joint `(alpha,lambda)` problem; retain y, X and C(lambda), including log determinant, whenever lambda is fitted.

## 2. Physical tensor chart and its actual identifiable quotient

Use signature `(-,+,+,+)`, U.U=-c^2, an observer-to-source spatial unit vector n, expansion H=Theta/3, shear sigma, vorticity omega, and acceleration A=∇_U U. The local directional expansion is

\[
\mathscr H(n)=H+\sigma_{ab}n^an^b-A_an^a/c.
\]

One derivation is to contract
`∇_b U_a = sigma_ab + omega_ab + H h_ab - U_b A_a/c^2`
with the future photon vector proportional to `U-cn`. The antisymmetric omega term vanishes; the spatial terms contribute `c^2(H+sigma:nn)` and the acceleration term contributes `-c A.n`. This fixes the acceleration sign for sourceward n. The relation governs the local first coefficient of luminosity distance, `d_L=cz/mathscr H(n)+O(z^2)`; a finite-redshift inversion also requires derivatives, transport, selection and a chosen congruence.

For ideal full-sky mathscr H,

\[
H=\langle\mathscr H\rangle,
\quad A_a=-3c\langle\mathscr H n_a\rangle,
\quad \sigma_{ab}=\frac{15}{2}\langle\mathscr H(n)(n_an_b-\delta_{ab}/3)\rangle.
\]

Actual masked sampled data must implement the corresponding response and covariance, rather than replacing these averages by unweighted catalogue sums.

R58's apparent chart is `alpha=(V3,d3,kappa5)`. The conditional physical map is

\[
V=c\beta,\qquad d=-a+d_{\rm cal},\qquad\kappa=s+q_{\rm cal},
\quad a=A/(cH),\ s=\sigma/H.
\]

The free-parameter physical state `(s5,omega/H[3],a3,beta3,d_cal3,q_cal5)` has 22 components and rank 11. Its kernel contains all three vorticity components, the simultaneous shift `(a,d_cal)->(a+u,d_cal+u)`, and `(s,q_cal)->(s+S,q_cal-S)`. These are exact statements for the declared local response. A likelihood for a directly named physical vector/tensor is legitimate; its nullspace must remain in the output. It is not legitimate to infer finite s or a bounds merely by deleting the calibration columns or applying a pseudoinverse.

An identifiable mixed functional can depend on `beta` and `s+q_cal`, for example `beta^T(s+q_cal)beta`. The analogous physical `beta^T s beta` is not invariant along the calibration fibre. Finite physical bounds require a stated constraint on that fibre, which leads to the construction below.

## 3. A physically interpretable calibration body

Let `h=(d3,kappa5)`, with the existing orthonormal Frobenius STF basis E_A, and the dimensionless calibration pattern

\[
b(n)=d_an^a+K_{ab}n^an^b,\quad K=\sum_A\kappa_AE_A.
\]

The exact angular moments are `<n_i n_j>=delta_ij/3` and
`<n_i n_j n_k n_l>=(delta_ij delta_kl+delta_ik delta_jl+delta_il delta_jk)/15`.
Odd cubic moments vanish. Since tr K=0,

\[
\langle b^2\rangle=|d|^2/3+2\|K\|_F^2/15=h^TGh,
\quad G=\operatorname{diag}(I_3/3,2I_5/15).
\]

Therefore use the explicitly declared body

\[
\mathcal B_\rho=\{\xi:\xi^TG\xi\le\rho^2\},
\quad B=G^{-1}=\operatorname{diag}(3I_3,15I_5/2).
\]

Here rho is a full-sky RMS angular log-distance calibration allowance. It is an O(3)-invariant physical field normalization, rather than an arbitrary Euclidean norm of mixed harmonic coefficients. It does not assert that the calibration is random or drawn from an isotropic distribution.

Distance modulus obeys `delta ln d_L=(ln10/5) delta mu`, so

\[
\delta\mu_{\rm RMS}=5\rho/\ln10=2.171472409516259\,\rho\;\mathrm{mag}.
\]

A small rho also approximates fractional distance RMS. A reported critical rho thus directly answers how much angular calibration would be sufficient to make the selected apparent anisotropy compatible with zero. This is an exact full-sky basis normalization, not the RMS over the survey's sky mask; the latter is a separate selection-weighted quantity. The ratio between dipole and STF budget can be varied as a declared sensitivity assumption if physically motivated.

## 4. Confidence sets and an exact bounded-calibration null calculation

Partition the full-rank Gaussian coefficient fit into V and h. With V unrestricted,

\[
J_{h\cdot V}=J_{hh}-J_{hV}J_{VV}^{-1}J_{Vh}
=[\operatorname{Cov}(\widehat\alpha)_{hh}]^{-1}.
\]

This retains all polar–STF and velocity correlations. The marginal/profile h estimate is hhat. Its eight-dimensional simultaneous 1-alpha confidence ellipsoid is

\[
E_h=\{h:(h-\widehat h)^TJ_{h\cdot V}(h-\widehat h)\le c_8^2\},
\quad c_8^2=\chi^2_{8,1-\alpha}.
\]

The physical null `a=s=0`, allowing calibration in B_rho and arbitrary V, means `h=xi in B_rho`. Define

\[
\delta^2(\rho)=\min_{\xi\in\mathcal B_\rho}
(\widehat h-\xi)^TJ_{h\cdot V}(\widehat h-\xi).
\]

Reject this bounded-calibration null when `delta^2(rho)>c8^2`. This is confidence-set inversion with size at most alpha uniformly over the calibration body. Indeed, if the true h is xi0 in B_rho, then `delta^2(rho) <= (hhat-xi0)^T J (hhat-xi0)`, and the right side has the stated chi-square law. **Delta itself is not generally chi-square distributed** under this composite constrained null. Calling it an exact chi-square likelihood-ratio distribution would be wrong; the threshold is conservative by set inclusion.

For `B=L L^T`, diagonalize `A=L^T J L=U diag(a_i) U^T` and set `nu=U^T L^-1 hhat`. Writing `xi=L U b`, the minimizing coordinates are

\[
b_i=\frac{a_i\nu_i}{a_i+\tau},\qquad
\sum_i b_i^2=\rho^2,
\]

when `||nu||>rho`. There is a unique tau>0 because the left side decreases strictly from `||nu||^2` to zero. If `||nu||<=rho`, tau=0 and delta=0. At rho=0, xi=0 directly. The objective is

\[
\delta^2=\sum_i a_i\left(\frac{\tau\nu_i}{a_i+\tau}\right)^2.
\]

The critical calibration is `rho_crit=min_{h in E_h} sqrt(h^T G h)`. This equals the existing convex gauge minimum Q_min with the explicitly physical RMS body and eight-dimensional radius. The new contribution is its source-bound measurement, not a claim to a new convex duality theorem.

For a finite union of declared nuisance models, use `E_union=union_m E_m`. The physical null is rejected only if every model excludes the body; equivalently `min_m delta_m^2>c8^2`. The first calibration needed for union compatibility is `min_m rho_crit,m`. Report the modelwise results as well as the envelope. The guarantee assumes at least one included working model and its Gaussian covariance are correct; arbitrary omitted systematics are not covered.

## 5. Physical support after bounded calibration

For the directly physical state `psi=(beta3,a3,s5)`, define

\[
\psi=T\alpha+K\xi,
\quad T=\operatorname{diag}(I_3/c,-I_3,I_5),
\quad K\xi=(0,d_{\rm cal},-q_{\rm cal}).
\]

The feasible confidence image is `T E_alpha + K B_rho`, a Minkowski sum, not a prior convolution. For any fixed dual direction u its exact interval is

\[
u^T T\widehat\alpha\ \pm\left[
 c_{11}\sqrt{u^TTJ^{-1}T^Tu}
 +\rho\sqrt{u^TKBK^Tu}\right].
\]

Use the 11D radius for simultaneous statements involving beta and the full apparent carrier; use the 8D marginal ellipsoid only when the target excludes beta and V is profiled. The vorticity coordinates remain unrestricted. For a nuisance union take the outer hull of these modelwise intervals; retain the union's representation to avoid confusing the hull with the exact set.

Tensor coordinate rotations act by `D=diag(R,D2(R))` on h; under parity the vorticity block is axial, det(R)R. Both covariance and precision transform, and declared body B must transform consistently. Survey masks can couple irreducible blocks; zeroing their cross-covariance is not implied by the ideal full-sky representation theory.

## 6. Covariance-amplitude variation does not give a monotone Wald frontier

For `C(lambda)=C_noise+lambda C_cosmic`, a PSD C_cosmic guarantees that a **fixed-mean** quadratic residual decreases as lambda increases. Its derivative is `-r^TC^-1 C_cosmic C^-1r <= 0`. The zero-mean omnibus `q0=y^TC^-1y` is one such residual.

The fitted-mean Wald statistic or difference between minimized residuals need not be monotone. A minimal exact counterexample is

\[
y=(0,1)^T,\quad X=(1,0)^T,\quad C(\lambda)=I+\lambda\begin{pmatrix}1&1\\1&1\end{pmatrix}.
\]

Its Wald statistic is

\[
W(\lambda)=\frac{\lambda^2}{(1+\lambda)(1+2\lambda)},\quad
W'(\lambda)=\frac1{(1+\lambda)^2}-\frac1{(1+2\lambda)^2}\ge0.
\]

It grows from zero although the covariance increases in Loewner order. Hence compute and retain the complete selected lambda curve; do not assume a unique crossing or infer a certified continuous worst case from a coarse grid. Monotonicity **in calibration allowance rho**, at fixed lambda and model, is valid by nested feasible sets.

If lambda is a nuisance range, the robust confidence set is the union over that range. A finite grid provides a finite sensitivity experiment; a continuous-range coverage claim needs an optimization or enclosure of all lambda. If lambda is inferred, retain the normalized likelihood and jointly profile the mean. The fixed-mean estimator repair below is not automatically a solution of the R58 free-mean profile problem.

## 7. An existing scientific code error and a constructive correction

The original `htt/obsstat/cf4_growth_covariance.py::amplitude_mle` states that the covariance-amplitude score is monotone and returns A=0 whenever score(0)<=0. Both the premise and resulting optimization rule are false.

For whitened positive covariance eigenvalues lambda_i and squared fixed residual components p_i^2,

\[
\ell(A)-\ell(0)=\frac12\sum_i\left[
\frac{p_i^2 A\lambda_i}{1+A\lambda_i}-\log(1+A\lambda_i)\right],
\]

\[
\ell'(A)=\frac12\sum_i\frac{\lambda_i(p_i^2-1-A\lambda_i)}{(1+A\lambda_i)^2},
\quad
\ell''(A)=\frac12\sum_i\frac{\lambda_i^2(1+A\lambda_i-2p_i^2)}{(1+A\lambda_i)^3}.
\]

The second derivative can have either sign. Set lambda=(100,1), p^2=(0,20). Then score(0)=-40.5 but `ell(1)-ell(0)=(10-log202)/2=2.3458661513>0`. The stationary points are

\[
A_\pm=(1699\pm\sqrt{2821801})/400,
\]

namely 0.04794570817 (local minimum) and 8.44705429183 (global maximum over the nonnegative domain). The latter gains 4.4485319395 in log likelihood over A=0. This is an implementation error on a legitimate PSD signal covariance, not a pathology caused by a failed cosmological model.

A finite global search domain follows directly from the score:

\[
U=\max\left(0,\max_{\lambda_i>0}\frac{p_i^2-1}{\lambda_i}\right).
\]

For A>=U each individual score term is nonpositive. Thus the constrained maximum on `[0,A_cap]` lies in `[0,min(U,A_cap)]`; zero eigenvalues contribute constants and must be handled separately. If all signal eigenvalues vanish, the amplitude is unidentified and the existing information variance is infinite.

A grid that brackets some score roots is not a guarantee of all roots. For low rank, multiply the rational score by the positive denominator `product_i(1+A lambda_i)^2`; every stationary point is a nonnegative real root of the resulting polynomial. This is a useful independent oracle for small manufactured cases, but polynomial conditioning makes it unsuitable as the general high-rank solver.

A practical bounded global method is interval branch-and-bound on the log likelihood. Each mode's term f_i(A) is maximized at `a_i=max(0,(p_i^2-1)/lambda_i)`. On interval [l,u],

\[
\sup_{A\in[l,u]}\ell(A)\le\sum_i f_i(\operatorname{clip}(a_i,l,u)).
\]

This is an analytic interval upper bound. Evaluated endpoint/midpoint/local-optimizer values give lower bounds. Split the surviving interval with largest upper bound until the global objective gap is below a declared tolerance. Always include endpoints, honor A_cap, reject nonfinite or materially negative eigenvalues, and report resource exhaustion as nonconvergence rather than silently calling a local candidate the MLE. Floating-point evaluation needs a roundoff allowance; an interval-arithmetic certificate should not be claimed from ordinary float arithmetic alone.

## 8. Typed roles of the five outputs and concrete acceptance checks

| Output | New result it can carry | Required meaning |
|---|---|---|
| x | full signed vector/STF likelihood and the physical map | Retain carrier, covariance, coordinates, units, epoch and identifiability |
| Q | RMS calibration distance to the confidence set, rho_crit | Declared full-sky RMS body and its physical units |
| Pi | named Gaussian test or conservative confidence-set inversion | Do not label composite delta^2 as exactly chi-square distributed |
| F_support | projected physical interval/support after bounded calibration | Support ratio can exceed one or be signed; it is not a probability |
| F_occupancy | fraction under an explicit support/measure and eligible ceiling | Remains unavailable if the measure or physical ceiling is absent |
| G_F | tensor depth path and its covariance-aware contrasts | Preserve initial level and every cross-depth covariance block |

The legacy `htt_five_variable_state.py` calls `h_I(u)/h_A(u)` an `occupancy_ratio`. This is historical naming; R58 correctly distinguishes F_support from F_occupancy. Do not reintroduce the conflation in new outputs. Its finite Fibonacci-grid docstring also overstates exact rotational invariance: the deterministic grid is quasi-uniform, not invariant under arbitrary rotations. Any numerical occupancy or optimized directional statistic must state quadrature/optimization error.

Meaningful acceptance checks are: likelihood equality against direct GLS in the same experiment; profile covariance identity; SO(3) equivariance of mixed blocks and body; analytic constrained result against an independent optimizer; monotonicity in rho; the PSD covariance/Wald counterexample; nonconcave amplitude likelihood and hard cap cases; and correct serialization of unbounded vorticity directions. Re-running unrelated governance checks does not address these mathematical obligations.

## Finite and symbolic evidence

`tensor_theory_checks.py` was executed with Python3, NumPy2.3.5 and SciPy1.17.0, seed6172026, exit0. It produced `tensor_theory_checks.json`:

- STF angular Gram discrepancy 2.78e-17 against the analytic fourth-moment contraction.
- Mixed rotation orthogonality, RMS metric and contraction errors <=6.67e-16.
- Profile-precision/marginal-covariance discrepancy 6.94e-17.
- Six constrained calibration budgets agreed with an independent SLSQP oracle to at most 7.07e-12 in objective; all oracle solves succeeded.
- The Wald/covariance counterexample and the exact two-mode amplitude roots were reproduced independently.

Wolfram Language independently returned the exact 8x8 angular Gram, exact Wald formula and derivative, the two-depth Gram determinant `(g1-g2)^2 w1 w2`, and exact amplitude stationary roots/log-likelihood gains. These are two computational routes for the stated algebraic/finite assertions, not a four-engine validation or a full observational likelihood audit.

## Publication consequence and limits

The framework's defensible contribution is an equivariant, uncertainty-preserving bridge from actual apparent tensor data to explicitly calibrated physical conclusions. The source-bound questions are: which vector/tensor combinations survive calibration uncertainty; how small an angular distance-calibration budget changes the selected conclusion; how much that answer depends on the cosmic covariance amplitude; and what information is lost by scalarization or dropped cross-block covariance.

This gives a measurable physical sensitivity result and an actionable estimator correction. It does not establish a new cosmological theory, increase information beyond the full specified likelihood, determine vorticity from scalar distances, identify a general Bianchi family, or turn a catalogue-selected tail into a discovery significance. The six scientific topics can share this bridge while retaining their distinct missing response/data obligations.
