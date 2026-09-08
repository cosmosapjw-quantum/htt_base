# R8 physics and statistics: derivations and decisive counterexamples

All new results below are analytical, with implementation and four-axis CAS obligations left to Local Codex. They extend the R7 equations under their stated domains, not the old seven-obligation CAS certificate. Literature supplies representation and radiation-hierarchy foundations; the orbit enclosures, rank stopping argument and joint-set application are derived here. No priority claim is made.

## O1. Useful lower bounds for a common-rotation tensor distance

For STF tensors `X=(Q,O)`, `Y=(Q',O')`, define

\[
d(X,Y)=\min_{R\in SO(3)} f(R),\qquad
f(R)^2=\|Q-RQ'R^T\|_F^2/q_0^2+
\|O-R^{\otimes3}O'\|_F^2/o_0^2.
\]

Let eigenvalues be sorted increasingly. Set `S(O)_ij=O_iab O_jab` and

\[
b_Q=\|\lambda(Q)-\lambda(Q')\|_2,\qquad
b_O=\|\sqrt{\lambda(S(O))}-\sqrt{\lambda(S(O'))}\|_2.
\]

Then

\[
\boxed{d\ge b_{\rm inv}=\sqrt{b_Q^2/q_0^2+b_O^2/o_0^2}.}\tag{O1}
\]

Proof. The symmetric spectral inequality bounds the quadrupole residual for every R. In its separate minimization the bound is attained even in SO(3), because an eigenvector sign corrects determinant without altering the diagonal tensor. Flatten O into the 3-by-9 matrix A. Rotation acts as `A -> R A (R tensor R)^T`, preserving singular values. The singular-value perturbation inequality bounds its Frobenius residual below by the difference of singular values. These are `sqrt(lambda(S))`. Both bounds hold for every **same** R, hence their squared combination is valid. Minimizing the two blocks independently does not assert simultaneous attainability.

An alternative Gram bound follows from `||AA^T-BB^T||F <= (||A||op+||B||op)||A-B||F`:

\[
b_{O,G}=\frac{\|\lambda(S)-\lambda(S')\|_2}
{\sqrt{\lambda_{\max}S}+\sqrt{\lambda_{\max}S'}}\le b_O.
\]

Define `0/0=0` only when both tensors are zero. The looser denominator `||O||F+||O'||F` is also valid. Bounds on the same residual combine by **maximum**, not sum of squares. Spectra are incomplete joint-orbit descriptors: relative Q/O alignment and signs can differ while both spectra agree.

**Exact fixtures.** (a) `Q=diag(-1,0,1), Q'=2Q, O=O'=0` gives `d=sqrt(2)/q0`. (b) The symmetric octopole with `O111=2, O122=O133=-1`, all other independent components zero, has norm squared 10 and `S=diag(6,2,2)`. With `Q=Q'=0, O'=2O`, `d=sqrt(10)/o0`; the singular bound is tight. (c) Keep `Q'=Q=diag(-1,0,1)` and rotate that octopole by the rational planar matrix with rows `(3/5,-4/5,0),(4/5,3/5,0),(0,0,1)`. Both bounds vanish but the joint distance is positive: the simple-spectrum Q stabilizer cannot map the octopole axis e1 to that rotated axis.

Plain floating eigensolver output is not a certified lower bound. Treat input binary64 entries as exact dyadic coordinates of the **computed statistic**, separately from measurement uncertainty. Isolate roots with multiplicities of the exact 3-by-3 characteristic polynomials, or use a validated eigenvalue enclosure. Lower differences use interval gaps; arithmetic, squares and square roots are outward. Overflow, nonfinite values or lost certification return unresolved, never an optimistic bound.

## O2. A quaternion cell certificate

Cover SO(3) using the four charts

\[
q_a(x)=\frac{e_a+\sum_{j\ne a}x_j e_j}{\sqrt{1+\|x\|^2}},
\quad x\in[-1,1]^3.
\]

Every unit quaternion has a component of maximal absolute value; using `q ~ -q` makes it positive and supplies one chart. Ties and chart overlaps do not create gaps. For a cell C with center c, half widths h, set

\[
r_C=\|h\|_2,\quad m_C=\sqrt{1+\sum_j\operatorname{dist}(0,C_j)^2},
\quad \delta_C=\min(\pi,2r_C/m_C).
\]

The normalized chart derivative has operator norm at most `1/m_C`; the line segment lies in C. Its spherical length is at most `r_C/m_C`, and rotation angle is at most twice that length. Thus `delta_C` is a valid rotation cover radius. A grid of spacing `1/m` has global radius `sqrt(3)/m`, with rational upper bound `7/(4m)`. This sharpens R7's `pi sqrt(3)/m` cover without changing the statistic.

The scalar residual norms yield the symmetric Lipschitz constant

\[
L=\sqrt{[2\min(\|Q\|,\|Q'\|)/q_0]^2+
[3\min(\|O\|,\|O'\|)/o_0]^2}.
\]

Each block may be bounded using forward or inverse rotation; these give its minimum-norm constant. Combine the two scalar inequalities by the Euclidean norm. If `f(center)` is enclosed by `[ell_c,u_c]`, a cell lower bound is

\[
b_C=\max(0,b_{\rm inv},\ell_c-L\delta_C).\tag{O2}
\]

All lower terms round down and `L delta_C` up. Feasible center or rationalized local-fit rotations provide upper bounds only. Maintain incumbent U, subdivide competitive cells, prune only when `b_C >= U`. The global lower is `min(U,min_active b_C)`, maximized with earlier certified lower bounds; if active is empty it is U. Incumbents decrease, so earlier pruned cells remain safe. Vanishing cell diameter and sufficiently precise enclosures imply continuous-optimization convergence; finite floating precision and exact ties may leave a nonzero floor. Runtime/power on the actual large pools is untested.

## O3. Interval ranks and adaptive numerical stopping

Fix a pool of M=N+1 exchangeable rows and exact permutation-equivariant scores

\[
s_i=\operatorname{kth}_{j\ne i}d(X_i,X_j),\quad k=\lceil\sqrt N\rceil.
\]

Symmetric pair enclosures `[ell_ij,u_ij]` imply `L_i=kth(ell_ij), U_i=kth(u_ij)` by coordinatewise monotonicity. For inclusive ties,

\[
p=\frac{1+\sum_{i=1}^N1[s_i\ge s_0]}M,
\quad
p^- =\frac{1+\sum_{i=1}^N1[L_i\ge U_0]}M,
\quad
p^+ =\frac{1+\sum_{i=1}^N1[U_i\ge L_0]}M.
\tag{O3}
\]

Then `p^- <= p <= p^+`. Endpoint equality is deliberate: `U_i=L_0` remains a possible inclusive tie. `p^-` is **not** a p-value. Under exchangeability, at most t rows in a fixed score multiset have inclusive descending rank at most t; averaging over the distinguished row proves `P(p<=alpha)<=alpha`. Consequently `P(p^+<=alpha)<=alpha`.

At any adaptive numerical stopping time tau, `p_tau^+ >= p` remains true pointwise. Observation-directed refinement therefore needs no optional-stopping penalty **for the fixed exact statistic**. This does not permit adapting scales, k, feature extraction, pool size, law, or testing family. Randomized enclosures need simultaneous failure probability at most delta over the entire refinement; then rejection at `p^+<=alpha-delta` controls size by alpha. Pointwise per-call enclosure probabilities do not suffice. Supporting finite-randomization context: [Hemerik–Goeman](https://arxiv.org/abs/1411.7565v3); the enclosure argument here is a direct proof.

At fixed alpha: `p^+<=alpha` certifies rejection; `p^->alpha` certifies non-rejection by this test; otherwise refine or report `[p^-,p^+]` and conservative `p^+`. Non-rejection is not acceptance of isotropy. Complete enclosures on an unqualified observational null are only rank diagnostics.

At alpha=1/20, M=1000 has k=32: at most 49 possible reference exceedances suffice for rejection, while at least 50 certain exceedances establish non-rejection. For M=301, k=18, the respective counts are 14 and 15. Use integer counts and `floor(M/20)`.

**Decisive counterexamples.** Scalar points `0,1,2,3,10` with k=2 have scores `2,1,1,2,8`. With the last observed, intervals `[0,3]` on references and `[7,10]` on it certify `p=1/5` without narrow scores. Conversely all exact scores zero, observed interval `[0,1]`, references `[0,0]`, require `p^+=1`. Ranking upper endpoints as if exact would falsely return `1/M`.

Initialize all pairs with invariant lower and feasible upper bounds regardless of M. Cache unordered pairs, tighten monotonically, select ambiguous comparisons to row 0, then pairs that can change their kth order statistics. A pair with `ell_ij>U_i` cannot change that kth distance. Budget exhaustion preserves valid intervals; absent input never becomes a valid interval.

## O4. Full multipole-vector equivalence and useful ablations

For real harmonic STF rank l, the representation is `T_l=A_l STF(v1 tensor ... tensor vl)` with unit vectors and amplitude. Vector sign/permutation freedom is compensated in A. The vectors are unidentified when amplitude is zero; reconstruction then returns the zero tensor. Full amplitude-preserving MV and Q/O are information-equivalent. Reconstructing the tensors and applying the same metric gives the same exact statistic, hence the same test. This follows the representation and uniqueness up to its freedoms in [Copi–Huterer–Starkman](https://arxiv.org/abs/astro-ph/0310511) and [Katz–Weeks](https://arxiv.org/abs/astro-ph/0405631).

For l=2, STF removes `delta_ij tr/3`. For a symmetric raw l=3 product A, `STF(A)_ijk=A_ijk-(delta_ij A_aak+delta_ik A_aaj+delta_jk A_aai)/5`. Freeze this amplitude convention before conversion. Tensor-to-MV uses the roots of the homogeneous harmonic polynomial restricted to the complex null cone, paired by the real-field antipodal relation; isolate/track multiple roots or return a conversion interval/refusal, without removing that row's original tensor. A conversion failure tests numerical reliability, not an absent sky.

Compare same rows: full tensors; full MV reconstructed tensors; existing cyclic packet where defined; power; normalized MV alignment; f_B. Full MV equivalence is the control. Potential scientific gains concern information discarded by the latter summaries and power against named alternatives, not extra information beyond the full harmonics. A signed diagnostic `chi=det(v,qv,q^2v)`, `v_i=o_ijk q_jk`, using dimensionless q=Q/q0,o=O/o0, is SO(3)-invariant and parity-odd. Nonzero chi witnesses lack of reflection invariance; zero alone does not classify the orbit. LRS coherent R3 has chi=0 even after a local boost; stochastic perturbations and asymmetric processing must be treated separately.

## J1. Confidence sets with incomplete dependence information

Let x retain physical/observable state, derivatives and shared calibration. Let `nu=(model,law,covariance,calibration,closure)` range over **compatible** admitted tuples. For each fixed measurement scope j require candidate-state acceptance `A_j,nu` with rejection probability <=alpha_j on its declared domain. Define

\[
\mathcal C(Y)=\bigcup_{\nu\in\mathcal A}
\left[\mathcal D_\nu\cap\bigcap_j\{x:A_{j,\nu}(Y_j,x)=1\}\right].\tag{J1}
\]

If the true tuple is in A, simultaneous acceptance under that tuple implies membership, so the union bound gives coverage at least `1-sum alpha_j`, with arbitrary cross-dependence. A random admission set containing the true nuisance with probability >=1-gamma changes the bound to `1-sum alpha_j-gamma`, without requiring independence. Missing fixed measurement scopes contribute the whole domain and retain their allocation. Alternative models/laws are unioned; measurements sharing one state are intersected. Correlated or contradictory assumptions must not be cross-multiplied into fictional tuples.

Project `I_g={g(x):x in C}` after construction. Letting each block choose a different shared calibration is an outer relaxation, never the exact shared-state set. An alternative with unrestricted nuisance can make the robust union unbounded; retain that result and display narrower conditional families separately. A union-null p-value is `sup_nu p_nu`; a finite grid maximum underestimates the required supremum unless certified between grid points. This is a standard nuisance-supremum principle, independently proved by containment of the true component.

## J2. A data-law capability ladder

Full normalized law gives direct confidence inversion. Known marginal blocks permit the J1 intersection. A known covariance-completion family `C>=0, C_jj=C_jj_known`, **together with an explicitly admitted joint Gaussian sampling family**, gives a union of candidate Gaussian regions. Gaussian marginals and covariance information alone do not imply a joint Gaussian law. Unknown cross-block entries are not zero by default.

If `Y_i ~ N(mu_i(x),v_i)` marginally with authenticated v_i>0, then

\[
|Y_i-\mu_i(x)|\le\sqrt{v_i}\Phi^{-1}(1-\alpha_i/2)\quad\forall i\tag{J2a}
\]

has coverage >=1-sum alpha_i under arbitrary dependence. With only `E Y_i=mu_i`, `Var(Y_i)<=v_i`, Markov gives

\[
\sum_i (Y_i-\mu_i)^2/v_i\le n/\alpha\tag{J2b}
\]

with coverage >=1-alpha. Proof: the expectation of the left side is at most n. Zero-variance coordinates instead impose exact deterministic equality; uncertain mean bias belongs in the nuisance set. These methods are conservative and cannot repair incorrect means or selection. CF4's quoted distance errors do not establish these laws for derived velocities conditional on observed distances. The [CF4 release paper](https://arxiv.org/html/2209.11238v2) describes multiple distance methods and their combination; the actual analysis must bind its chosen measurement/conditioning product.

For an exact Gaussian member, acceptance is `r in range(C)` and `r^T C^+ r <= chi2_rank(C)(1-alpha)`. This is candidate-state inversion; do not subtract fitted parameter count. Floating eigensolver zero is not a structural support certificate. A factor representation `C=B V B^T`, B known full-column-rank and V positive definite, supports a reduced experiment: require `r in range(B)`, set `z=B^+r`, and use `z^T V^-1 z`. Support-uncertain rounded products require an admitted model of the rounding/uncertainty or conservative unresolved membership, not jitter disguised as measurement noise.

## J3. Shared calibration is counted once

Fixed eta in `Y=F theta+Z eta+epsilon` is a nuisance in a normalized conditional law. A declared random effect `eta~N(m,S)` independent of `epsilon~N(0,N)` instead gives `Y~N(F theta+Zm,N+ZSZ^T)`. If calibration observations `c=H eta+nu`, `nu~N(0,V)`, share that eta, and eta, epsilon and nu are mutually independent in this baseline model, the joint covariance is

\[
\begin{pmatrix}N+ZSZ^T&ZSH^T\\HSZ^T&V+HSH^T\end{pmatrix}.\tag{J3}
\]

Other shared measurement noise adds its actual cross terms. Reusing c both for an independent prior and as another likelihood doubles information. If c has mean response `B theta`, the conditional Y response is `F-C_Yc C_cc^+ B`; keep `p(c|theta)` unless the experiment is explicitly conditional or c is ancillary. Existing R7 Schur-gain and duplicate-row formulas remain the implementation donors. Calibration data improve the physical direction only when their response constrains its coupled nuisance; DESI compressed qiso is not a directional or radiation-jet measurement merely because it informs the background.

## P1. Tensorized MES with genuine remainder propagation

Use geodesic radiation observers, collisionless photons, and **first order about FLRW**, including geometric departures, temperature gradients and their derivative ordering, with R7's rate derivatives/antisymmetrization. Small radiation anisotropy alone is not sufficient to discard kinematics-times-multipole terms. For outward normalized moments `q=Q/Tbar`, `d=Dsky/Tbar`, `o=O/Tbar`,

\[
\sigma=-\dot q+\operatorname{STF}(Dd)+\tfrac37\operatorname{div}o+R_\sigma,
\quad
\omega=\tfrac3\Theta\dot C_{out}+C_{out}-\tfrac6{5\Theta}E+R_\omega,\tag{P1}
\]

where `Cout=D_[a d_b]`, `E=D_[a D^c q_b]c`. All terms are rates. Differentiate the temperature normalization. The FLRW-linear equations (101)–(102) in [Maartens–Gebbie–Ellis](https://arxiv.org/html/astro-ph/9808163v2) supply the hierarchy; (97)–(98) display terms retained in the broader small-anisotropy treatment. The vorticity expression follows by the geodesic curl and FLRW commutator. Explicitly, outward `D log T=dot d-(2/5)div q`, `D_[a dot d_b]=dot C_ab+(Theta/3)C_ab`, and `D_[a D_b]log T=(Theta/3)omega_ab` give P1. These equations do not measure the jet from one sky. Broader domains require admitted bounds on omitted couplings and their differentiated/commutator contributions; acceleration or scattering needs its additional terms.

In orthonormal STF and antisymmetric bases collect normalized derivatives as j; then `vec(S,W)=K j+r`, `r=vec(Rsigma,Romega)/Theta`. The current `r7_radiation_jet.kinematics_from_radiation_jet` reads a remainder bound but returns only the center tensors. R8 adds a set-valued layer: for `j=j0+L u, ||u||<=rho` and independent admitted remainder set R, its support is

\[
h(a)=a^TKj_0+\rho\|L^TK^Ta\|+h_{\mathcal R}(a).\tag{P2}
\]

This follows by Cauchy–Schwarz with equality in the u direction; it is exact for the declared ellipsoid plus Minkowski remainder set. Additional dynamics/integrability constraints can shrink the set, making this a certified outer support. L is a deterministic budget operator unless it has actual covariance provenance. For independent remainder balls with rate radii r_sigma,r_omega, `h_R(a)=(r_sigma||a_S||+r_omega||a_W||)/Theta`; Θ uncertainty must stay in the state, or an explicitly conservative positive lower bound is used.

The scalar outer bounds become

\[
\|S\|\le\epsilon_2^*+\epsilon_1'+3\sqrt3\epsilon_3'/7+r_\sigma/\Theta,
\quad
\|W\|\le3\epsilon_1^{\prime *}+\epsilon_1'+6\epsilon_2''/5+r_\omega/\Theta.
\tag{P3}
\]

Envelope meanings are exactly R7 T3c. Compute s2,w2 and legacy comparison/depth coordinates from the common J1 set, not unrelated maxima. If using `G_F=F_far-F_near`, both F values use one admitted state/calibration/denominator domain. Vanishing denominators return a domain result; the finite `s2,w2` result can survive.

## P2. Closure frontiers and limits of inference

For linear observation R and tensor map K, a feasible state x and a recession direction `v in rec(D)` with `Rv=0, Kv!=0` give the family `x+t v`: same observation, diverging tensor target. This proves unbounded nonidentification **within the admitted local state domain**. It does not prove arbitrary jets extend to a global Einstein–Boltzmann solution. For a specific functional a, require `a^TKv!=0`; some targets can remain bounded even when others do not.

Use a nested closure family `D(rho)` of derivative/remainder budgets, plus an explicitly unrestricted local-jet comparison. Set inclusion makes every projected interval widen monotonically with rho. For a declared threshold g0, report `rho_crit=inf{rho:g0 belongs to I_g(rho)}`, with interval/infinite/unresolved status and certified bracketing where available. This is a **sensitivity frontier**, not a posterior on rho or a data-selected physical prior. Compact jets, bounded remainders and `Theta>=Theta_min>0` give finite continuous tensor images. Expanding H0–H3 nuisance alternatives can undo that bound; report the union and each conditional family.

An R3 provider can supply a restricted dynamical closure, reusing [R3_MODEL_REFERENCE.md](../tensor_joint_r7/R3_MODEL_REFERENCE.md). Its vorticity zero and coherent mirror symmetry are controls. The small-velocity FLRW response remains `f_o=(1+z)c/[H chi_r]`, `f_g=(1+z)(1-f_o)`, and `f_g/f_o=-1+(1+q_dec,0)z^2/2+O(z^3)`. Here the deceleration `q_dec,0` is not the orbit scale q0. Response rank after actual covariance and nuisance projection determines distinguishable local/global combinations. More redshift bins alone do not guarantee usable separation.

## N1. Non-Gaussian and selected-data continuation

For a fixed-count selected block with measured y, latent xi and shared Z/eta, use a finite positive normalization:

\[
p_{sel}(y|\theta,\eta,Z)=
\frac{s(y)\int\lambda(\xi|\theta,Z)p(y|\xi,\theta,\eta,Z)d\xi}
{\int s(u)\int\lambda(\xi|\theta,Z)p(u|\xi,\theta,\eta,Z)d\xi du}.\tag{N1}
\]

Correlated blocks remain joint; random Z/eta are integrated once. A numerical quadrature error estimate is not certified coverage. If an exact simulator of the candidate conditional experiment exists, apply the full fitting/scoring/selection procedure symmetrically to observation and simulated rows and use a valid rank test. Simulated mocks of another product or selected after inspecting the observation do not qualify.

A finite grid calibration establishes only its stated grid and procedure; continuum confidence requires an exact pointwise acceptance construction or certified control between points. Uncalibrated candidates remain in an outer confidence set. Gaussian checks, valid algebra and six-page PDF inspection do not substitute for non-Gaussian calibration. Validation fixtures and finite campaigns are frozen in VALIDATION_MATRIX; observed qualification remains per product.

## Literature and history consequences

The general Lorentz operator and inability to infer primordial dipole amplitude from low multipoles are addressed by [Chluba–Ravenni](https://arxiv.org/abs/2505.02080). [Notari–Quartin](https://arxiv.org/abs/1504.02076) requires product-specific kinetic quadrupole handling. Neither licenses a processed Planck beta fit using only the ideal Q-to-O response. The inherited full-sky adapter is useful as a controlled oracle; the product response remains explicit. [AniLoS/AniCLASS](https://arxiv.org/abs/2506.07786) is an optional supported-mode comparison, never a substitute for unavailable channels.

This combines the old HTT/MIO observer diagnostics, tensorized MES, source-nuisance competition and BASS dynamics into a single evidence graph. It does not rehabilitate old likelihood/evidence numbers whose generating laws were invalid. Reusable equations, adversarial counterexamples, operator code and real data intake survive independently of those historical claims.
