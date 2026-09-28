# R7 mathematical, physical and statistical research

Status: analytical derivations and design propositions, subject to the independent review recorded in `state/DECISION_LOG.md`. No new numerical values, CAS passes or observed estimates are asserted here. Standard facts are attributed; novelty is a question about the complete application, not an automatic consequence of a new notation.

## T1. Full tensors, invariant summaries and singular strata

Let `V=STF2(R³) ⊕ STF3(R³)` with Frobenius inner products. The observation carrier retains 12 real coefficients and an absolute frame. On nonzero cyclic pairs, the existing 16-contraction packet plus two amplitudes reconstructs the SO(3) orbit. This is an overcomplete constructive chart, not a minimal global coordinate system. The repaired inverse at Q must be integrated into H; its forward-image/contraction/replay checks are part of the inverse contract.

For fixed unit q, let `L_q o=o:q` and `M_q=I+6q²/5`. Existing algebra gives

\[
L_qL_q^*=M_q/3,\qquad
F_q(v)=R_qv+\sqrt{1-3v^TM_q^{-1}v}\,S(\ker L_q).
\]

The minimum-norm right inverse is `R_q=3 L_q^* M_q^-1`. The fibre is nonempty for `3v^T M_q^-1 v<=1`: strict interior gives S³, equality a singleton, and outside gives the empty set. Therefore power plus the contraction vector, and a fortiori `f_B`, do not fix the full shape. This is a concrete reason to keep full tensors in the likelihood and use the packet as a summary. Multipole vectors already preserve harmonic information; [Copi et al.](https://arxiv.org/abs/astro-ph/0310511), [Katz–Weeks](https://arxiv.org/abs/astro-ph/0405631), and [Land–Magueijo](https://arxiv.org/abs/astro-ph/0502574) are comparison baselines. The last title was misattributed to Katz–Weeks in R2's bibliography; the author attribution is corrected here.

An all-strata observable distance, with fixed positive scales q0,o0, is

\[
d([X],[X'])=\min_{R\in SO(3)}
\sqrt{\|Q-RQ'R^T\|_F^2/q_0^2+
\|O-R^{\otimes3}O'\|_F^2/o_0^2}.
\tag{T1}
\]

Compactness gives an attained minimum; orthogonal invariance gives the quotient metric. Zero distance means one common proper rotation maps both tensors. It is defined at zero amplitudes and repeated eigenvalues. It preserves mirror distinctions when the orbits differ. Absolute directions are retained separately in the original carrier and joint likelihood. In particular, `chi=0` does not imply achirality outside the cyclic chart.

**Fixed verification witness:** Q=diag(-1,0,1), with symmetric O components in order `(111,112,113,122,123,133,222,223,233,333)` equal to `(1,0,0,-2,1,1,1,-1,-1,1)`. Trace contractions vanish, `O:Q=(0,-1,1)`, chi=0, and no proper rotation maps `(Q,O)` to `(Q,-O)`. Distinct Q eigenvalues restrict its stabilizer to signed eigenaxes; all O_iii=1 force the required map to invert all three axes. This is an exact adversarial test, not an observed sky.

For a declared fixed global-rotation grid of covering radius delta in rotation angle, the unsquared distance has Lipschitz constant
`L=sqrt((2||Q'||/q0)^2+(3||O'||/o0)^2)`. Thus `max(0,d_grid-L delta) <= d <= d_grid`. Local minimization can improve the upper bound but never establishes the lower bound. Use these intervals to certify any claimed distance/rank precision; refine only unresolved comparisons. With scalar grid-evaluation error bounded by e, use max(0,d_grid-e-L delta) and d_grid+e; refinement, tie resolution and stopping must be permutation-equivariant across all pooled rows. A grid with no certified covering radius or evaluation-error bound gives an approximation diagnostic.

## T2. Full-shape null and scalar ablation

The full-shape test uses T1 distances among the observed row and the fixed null pool. Fix `k=ceil(sqrt(N))`, q0 and o0 from the declared null theory or an independent training pool. Each of the N+1 rows receives the kth nearest-neighbour distance to the other N rows. The algorithm is permutation-equivariant and defined even when the inverse chart is unavailable. Equal scales/data-independent definitions are used for all rows. Numerical distance ambiguity must be resolved or the exact-rank lane returns `NUMERICALLY_UNRESOLVED`; other science lanes continue.

This is a particular full-orbit outlier diagnostic, not a claim that one scalar is sufficient against every alternative. Its power is compared with full harmonic likelihood fits, packet distances on their common domain, multipole-vector statistics, `(C2,C3)` and f_B under registered alternatives. The full carrier remains the inferential input regardless of the score selected.

The known ideal benchmark is
\[
f_B=\|P_QO\|^2/\|O\|^2,\quad
f_B\mid Q\sim{\rm Beta}(3/2,2),\quad
F(x)=\tfrac52x^{3/2}-\tfrac32x^{5/2},\quad E f_B=3/7.
\tag{T2}
\]
It requires Q≠0 and an independent centered spherical Gaussian STF3 O. This follows from independent chi-square sums of dimensions 3 and 4; it is not the masked PR3 null law. `f_B` is a response projection fraction, not a fraction of kinematic origin. Q/O zero amplitudes use a typed unavailable scalar while full tensors remain available.

## T3. Physical tensorized MES before scalar ceilings

Use geodesic radiation observer `u`, expanding background `Theta>0`, collisionless photons, and first order about an isotropic radiation background. The photon **propagation** direction e is opposite to outward sky n. With brightness temperature coefficients vartheta in e, the observed full-sky local coefficients satisfy `vartheta_2=Q/T0`, `vartheta_3=-O/T0`, `vartheta_1=-D/T0`. If outward coefficients are used directly, transform every odd moment and its derivative consistently. A removed observed dipole is not zero physical vartheta_1.

With rho an energy density and physical energy flux `F_a=c q_a`, brightness moments are
\[
q_a=\tfrac43\rho\vartheta_a,\quad
\pi_{ab}=\tfrac8{15}\rho\vartheta_{ab},\quad
\xi_{abc}=\tfrac8{35}\rho\vartheta_{abc}.
\]
The latest Appendix E provides this restricted physical closure. Cancel background radiation evolution before taking norms. The tensor relations become
\[
\sigma_{ab}=-\dot\vartheta_{ab}-D_{\langle a}\vartheta_{b\rangle}
-\tfrac37D^c\vartheta_{abc},
\tag{T3a}
\]
\[
C_{ab}=D_{[a}\vartheta_{b]},\quad E_{ab}=D_{[a}D^c\vartheta_{b]c},\qquad
\omega_{ab}=-\frac3\Theta\dot C_{ab}-C_{ab}-\frac6{5\Theta}E_{ab}.
\tag{T3b}
\]
Here `dot=c u^a nabla_a` and `D_a=c h_a{}^b nabla_b` use rate units (u is unit timelike). Define `omega_ab=c h_a{}^c h_b{}^d nabla_[d u_c]`, the convention giving `D_[a D_b]phi=-omega_ab dot(phi)`. Antisymmetrization includes 1/2. C has s⁻¹; E and dot C have s⁻²; E/Theta and dot C/Theta have s⁻¹. Every additive term on the right of T3a/T3b is consequently a rate. A code that defines vorticity with the opposite index order must flip the signed tensor at the adapter. Acceleration-free is a premise of T3b. Reopening accelerated congruences requires the acceleration curl and its own likelihood/derivative envelope; do not silently insert a geodesic identity there. Coefficients follow the displayed brightness hierarchy and angular moments, rather than copying an isolated differently normalized integrated equation from the literature.

For the outward-sky implementation, put `d=D_sky/Tbar`, `q=Q/Tbar`, `o=O/Tbar`. Then `sigma=-dot(q)+STF(D d)+(3/7)div(o)` and `omega=3dot(Cout)/Theta+Cout-6D_[a D^c q_b]c/(5Theta)`, where `Cout=D_[a d_b]`. Differentiate the normalized coefficients, including Tbar: `dot(Q/Tbar)` is not `dot(Q)/Tbar`. A coefficient-level primary reference is [Maartens–Gebbie–Ellis, equations (89),(93)](https://arxiv.org/html/astro-ph/9808163v2).

The first-order remainders `R_sigma,R_omega` are zero within the truncated mathematical model. Applying it to finite physical perturbations requires additional valid bounds on these remainders. In their absence output a first-order model-conditional result.

With envelopes for the **specified** derivative operators, triangle inequalities give the sharpened sufficient bounds
\[
\|\sigma\|/\Theta\le\epsilon_2^*+\epsilon_1'
+3\sqrt3\epsilon_3'/7,
\quad
\|\omega\|/\Theta\le3\epsilon_1^{\prime *}+\epsilon_1'
+6\epsilon_2''/5.
\tag{T3c}
\]
Explicit envelope definitions are `epsilon2_star >= ||dot(vartheta2)||/Theta`, `epsilon1_prime >= ||D vartheta1||/Theta`, `epsilon3_prime >= ||D vartheta3||/Theta`, `epsilon1_prime_star >= ||dot(D vartheta1)||/Theta²` and `epsilon2_doubleprime >= ||E||/Theta²` with projected derivatives and the declared first-order commutators. They are upper envelopes, not automatically measured quantities.

The first bound uses `||div vartheta_3|| <= sqrt(3)||D vartheta_3||`. The double-prime bound is on E itself, not on a differently normalized derivative tensor. These can be tighter than uncancelled Appendix E envelopes under the same model. They are not new empirical limits. [MES 1995](https://arxiv.org/abs/astro-ph/9501016) and [Saadeh et al.](https://arxiv.org/abs/1605.07178) concern different assumption sets; a numerical scale comparison must label the changed premises.

Retain the radiation derivative jet J and its cross-covariance. Define physical X=(sigma/Theta,omega/Theta,tilt,curvature,J) with the tensor equations and allowed jet set. Build joint sets in X, then evaluate s2,w2, tensor alignments, handed contractions and the legacy comparator in the same X. Replacing this by independent upper-bound balls loses directions and coupled feasibility. Derivative-envelope coefficients are sensitivity axes until external/physical information measures them; a single sky cannot fill the missing jet.

## T4. Four nuisance experiments, not four interchangeable answers

At a declared linearization let `y=A theta+K h+n`, with positive noise covariance N. A is the actual parameter Jacobian; K is the derivative with respect to the high-source nuisance in this experiment. In a boost problem both may depend on the background sky and beta, so this local form never substitutes for the full forward model.

**H0:** Unrestricted deterministic h gives the whitened quotient response `(I-P_(N^-1/2 K))N^-1/2 A`. Kernel directions are nonidentified in the declared unrestricted experiment.

**H1:** Let `h=h0+S^(1/2)u`, `||u||<=rho`, S positive definite. For a fixed required residual d in the range of K,
\[
c(d)=d^T(KSK^T)^+d,
\quad c(d)=+\infty\text{ outside the range}.
\tag{T4a}
\]
Cancellation from h0 is feasible iff `c(d)<=rho²`. Overlap of two allowed parameter mean sets instead uses the difference of two nuisance balls and the threshold **4 rho²**. Treating the latter as rho² is an incorrect identifiability test. A temperature-positivity restriction further intersects the feasible set; it cannot enlarge it.

**H2:** For independent Gaussian `h~N(h0,S)`, `n~N(0,N)`, the marginalized law has mean `A theta+K h0`, covariance `C=N+KSK^T`. If beta changes the response or covariance, its Gaussian Fisher information contains both terms:
\[
F_{ij}=\mu_{,i}^TC^{-1}\mu_{,j}
+\tfrac12\operatorname{tr}(C^{-1}C_{,i}C^{-1}C_{,j}).
\tag{T4b}
\]
At zero mean an even covariance may distinguish magnitude while leaving a sign degeneracy. H0 rank zero is not a no-information theorem for H2.

**H3:** Additional measured modes z enter the **joint** law. For a joint Gaussian (y,z), with means `A theta` and `B theta`,
\[
y\mid z,\theta\sim N\big[A\theta+C_{yz}C_{zz}^{-1}(z-B\theta),
C_{yy}-C_{yz}C_{zz}^{-1}C_{zy}\big].
\tag{T4c}
\]
When `W=C_yz C_zz^-1` is parameter independent, the conditional parameter response is `A-W B`, as well as a changed covariance. Generally its derivative is `mu_y,i-W mu_z,i+W_,i(z-mu_z)` and the conditional covariance derivative must also be retained. Keep `p(z|theta)` unless z is genuinely ancillary or the inferential target is explicitly conditional. For singular Czz use its support and exact null constraints. The same-map high-mode data are not an independent prior observation. If z is exactly a function of already consumed y, it adds no information.

The four branches answer an assumption-sensitivity question. A union over maintained model confidence sets is conservative for uncertainty over those models; their intersection is not. A max of valid model-wise p-values tests a union null. A min selects a favorable assumption and has no such robustness interpretation.

## T5. A finite-band small-mask result: rank versus practical ambiguity

Take exact continuum real harmonics y for ell=0..5 (36 entries), and g for the first-order boost response of source ell=7..L at fixed finite L. Isotropic beam operations preserve ell. Full-sky nearest-neighbour boost coupling gives `integral yg^T=0`. Let mask weight `w=1-m`, `0<=m<=1`, `f=(4pi)^-1 integral m`. Fit all 36 before a fixed retain/commonization matrix C produces 32 outputs.

The addition theorem gives `||y(n)||²=36/(4pi)`. Consequently, for `G_w=I-E`, `E=integral m yy^T`, one has `||E||<=tr E=36f`. If `f<1/36`, G_w is positive definite and
\[
\|K_w\|\le\frac{c_L f}{1-36f},\qquad
c_L=\|C\|4\pi\sqrt{36/(4\pi)}\sup_n\|g(n)\|,
\quad K_w=C G_w^{-1}\int w yg^T.
\tag{T5a}
\]
For `0<f<1/36`, `c_L>0`, and any fixed nonzero cancellable d,
\[
\min_{K_w\delta h=d}\|\delta h\|^2
\ge\frac{\|d\|^2(1-36f)^2}{c_L^2f^2}.
\tag{T5b}
\]
Proof: `integral w yg^T=-integral m yg^T`; bound its norm by `4pi f sup||y|| sup||g||`, apply the inverse Gram bound, then `||d||<=||K_w||||delta h||`. If f=0 or K=0 the cost for nonzero d is infinite. For an ellipsoid budget replace g by `g S^(1/2)` to bound minimum whitened nuisance cost; the Euclidean coefficient bound alone is not a measured physical budget. Thus a full-rank branch can still become practically unable to cancel a fixed signal as the mask shrinks. The argument neither proves full rank for all masks nor interchanges `L→infinity` with `f→0`.

Exact implementation oracle for a soft family `m=t m0` is
`K(t)=-t C(I-t E0)^-1 A0`, `K'(0)=-C A0`, where `A0=integral m0 yg^T`. Binary shrinking masks satisfy the inequality but not this fixed-mask derivative identity. Pixel quadrature, nonlinear component separation and higher boost orders require explicit additional error terms. This is a new application-level derivation for the campaign, built from standard harmonic/norm identities.

## T6. Calibration-only data can improve physical inference

For a regular local Gaussian experiment with common nuisance eta, write Fisher blocks
`F0=[[U,V],[V^T,E]]`, E positive definite. Independent additional calibration measures eta only, contributing G positive semidefinite to E. Efficient information for theta changes by
\[
\Delta F=V[E^{-1}-(E+G)^{-1}]V^T\succeq0.
\tag{T6}
\]
For direction a, the gain is zero iff `G^(1/2) E^-1 V^T a=0`. Factor the inverse difference through `E^-1/2[I-(I+E^-1/2 G E^-1/2)^-1]E^-1/2` to prove positivity and its kernel. A proper nuisance identification/gauge is required; a pseudoinverse alone does not establish the same formula at singular E.

This connects legacy JWST host contrasts with CF4/anchor inference. A same-host contrast cancels the common geometric distance in its mean, so alone it need not constrain geometry. It can still constrain a calibration variable coupled to the distance data. If no authenticated calibration link exists, G does not belong to the same E and this gain cannot be claimed. Shared measurement noise also requires joint conditioning before using the independent-increment formula. This is a standard Schur-complement fact used to recover a concrete project role for calibration data.

## T7. Joint confidence images, tensor invariants and GF

Let a simultaneous `1-alpha` confidence region `C_Y` cover the full observable mean/state variable used in the forward law. Let F_eta be the declared physical/jet domain and R_eta its observation response. Define
\[
\Theta_Y(\eta)=\{X\in F_\eta:R_\eta(X)\in C_Y\},\qquad
I_Y(\eta)=\{g(X):X\in\Theta_Y(\eta)\}.
\tag{T7}
\]
On the event that C_Y contains the true response and the maintained model contains the true state, the true g(X) lies in I_Y. This is the entire coverage proof; realized feasibility alone provides no coverage. If a separate `1-gamma` nuisance confidence region is used, union over it gives coverage at least `1-alpha-gamma`, without an independence requirement. Deterministic physical premise sets are assumptions, not extra measured evidence.

For exactly observed linear y, the compatible set is a constrained affine kernel fibre. With nonzero observational uncertainty it is an inverse image of C_Y, not `X0+ker R`. Project all quantities jointly. In particular evaluate near/far F on the same X and form their registered signed depth gap before optimizing extrema; separately combined endpoint bounds may still be conservative outer bounds, but generally are not attainable joint extrema. Reuse GF v8/v9 for its affine/positive-denominator domain and propagate residual/nonlinear optimization error elsewhere. Return `DENOMINATOR_UNRESOLVED` when positivity of the ratio denominator is unproved.

### T7b. Different measurements with unknown cross-dependence

For fixed data scopes j=1,...,J under one shared physical model, suppose each marginal confidence region satisfies P_theta(theta not in C_j)<=alpha_j uniformly over the maintained nuisance domain. Then P_theta(theta not in intersection_j C_j)<=sum_j alpha_j by the union bound. Independence is unnecessary. This is a joint confidence construction from marginal coverage, not a normalized joint likelihood. Fixed missing/unqualified scopes may contribute the full parameter domain; do not reallocate their error budget after inspecting results. Certified outer approximations preserve this conclusion. Alternative physical/nuisance models still require the union construction above, since their premises are disjunctive rather than simultaneous measurements. OWNED_ASSETS binds the fixed error allocation and consumers.

## T8. Finite nulls, nuisance uncertainty and branching

With an exchangeable observed+reference pool and a row-equivariant complete procedure,
`p=(1+sum_j 1[S_j>=S_0])/(N+1)` is conservative over the joint random generation of the bank and observation (or under a justified symmetric conditioning). It does not assert conditional validity for an arbitrary realized bank frozen after generation. The whole procedure includes feature extraction, fit/refit, chart fallback and the registered statistic/mask/model-selection rule. Same code is insufficient if the joint law is not exchangeable. See [Hemerik–Goeman](https://pmc.ncbi.nlm.nih.gov/articles/PMC6405018/).

For K diagnostics under one null law, use a predeclared max score whose normalization is independent or permutation-equivariant, and rank that max score on every row. Alternatively use a finite-sample valid Bonferroni correction. Robustness across null **laws** uses a supremum, not the max-statistic construction for choices under one law. For nuisance confidence region C_gamma, the Berger–Boos construction `min(1,sup_(eta in C_gamma) p_eta+gamma)` is valid when each p_eta is valid and C_gamma covers the true nuisance. A finite grid maximum is only a lower approximation to the required supremum unless an upper approximation error is certified. See [Berger–Boos, 1994](https://doi.org/10.1080/01621459.1994.10476836).

If empirical nuisance refitting or simulator mismatch prevents an exchangeability proof, the output is an approximate calibrated test with measured coverage/FPR on a specified experiment, not an exact finite-null p-value. The old 999 rows with repeated noise cannot be promoted by their row count. Unsupported tails, unresolved rows and lack of joint simulator are typed limitations of their particular test branch.

## T9. Dynamics, depth and historical ideas

The R3 counterstream model is an oracle for constrained dynamics, not a universal morphology generator. `a_perp=a exp(-b)`, `a_parallel=a exp(2b)`, `S=dot b`, `H_parallel=H+2S`. Each dust stream conserves `a_parallel sinh chi=kappa`, so `dot chi=-H_parallel tanh chi` and `dot beta=-H_parallel beta(1-beta²)`. Opposite equal streams cancel total flux while preserving positive anisotropic stress. Reuse `bi_continuation`, not the incompatible finite-rapidity evolution in the older nonperturbative module.

Its Einstein equation is `H²=8pi G epsilon/(3c²)+Lambda c²/3+S²`, `dot S=-3HS+8pi G(p_parallel-p_perp)/(3c²)`. Collisionless radiation requires its actual angular stress integral; an isotropic perfect fluid replacement is a different model. Existing ray transport plus the Jacobi equation `D''=-R(screen,k,screen,k)D`, `D(0)=0`, `D'(0)=I` yields distances only after screen/affine conventions and reciprocity are validated. `1+z=E_s/E_o`, `D_L=(1+z)² D_A` must use consistent emitter and observer frames.

In the flat FLRW small-velocity limit at fixed observed redshift,
\[
\delta\mu={5\over\ln10}\,n\cdot[f_o(z)\beta_o+f_g(z)K],\quad
f_o={(1+z)c\over H\chi_r},\quad f_g=(1+z)(1-f_o),\quad
\chi_r=c\int_0^zH^{-1}dz',
\]
\[
f_g/f_o=-1+\tfrac12(1+q_0)z^2+O(z^3),\qquad
\det F=(\sum_i w_i f_{o,i}^2)^2\operatorname{Var}_{p}(f_g/f_o).
\tag{T9}
\]
The determinant formula is for one spatial component and independent scalar weights `p_i ∝ w_i f_o,i²`; actual surveys use the full covariance and nuisance-projected response. The expansion needs all velocity/frame redshift shifts small compared with z. Many shallow bins can remain nearly degenerate. Data-dependent redshift conventions and empirical depth multipliers do not replace these functions.

Reflection/inversion symmetry of the R3 normal sky produces vanishing odd moments, and its LRS coherent sky remains nonchiral after an arbitrary observer boost. Adding a stochastic sky changes that statement for the total observed realization. The benchmark therefore checks symmetry limits; it cannot alone calibrate arbitrary handed morphology. Merely making the scale factors triaxial does not break an inversion-symmetric initial photon distribution.

For more general supported templates use external near-isotropic transfer with declared modes and initial conditions. [Vicente–Pereira–Pitrou](https://arxiv.org/html/2506.07786v2) supplies AniLoS/AniCLASS for selected regular vector/tensor modes; the public implementation does not supply all scalar/initial-condition branches. Its metric anisotropy beta_ij is distinct from rate shear. A transfer-specific conversion and reference replay are mandatory. This is an external donor, not authenticated native BASS delivery.

Other productive recoveries are explicit: old Axis-C q+d experiments become exact deprojection/calibration controls with their true cross term and finite-noise variance; CF4 constrained realizations test longitudinal bulk/shear recovery but cannot manufacture curl outside their prior/response support; x_C cancellation examples motivate joint tensor feasible sets; Teff/TSC guards become common semantic checks with their old numerical claims retained as historical claims, not new evidence.
