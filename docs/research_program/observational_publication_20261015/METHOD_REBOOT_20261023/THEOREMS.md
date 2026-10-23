# Solver-free tensorized inference: derivations and statistical contracts

Owner: HTT/MIO/obsstat research, 2026-10-23. Source snapshot: PR561 `cd2bf729f12a4229f0bb423850372a511dcff78b`. This is a new conditional-method investigation. Original external-output acceptance is 17/42; the V03 analytic-alternate accounting is 18/42. Neither count changes here. No Einstein–Boltzmann solver or ODE was built or run.

The results below specialize established geometry, linear algebra and statistical principles. Their HTT combination and the K03 retained-summary calculation are the present contribution; a literature-novel theorem or submission-ready paper is not asserted. Detailed primary-source comparisons are in `agent_observables.md` and `agent_selection.md`.

## Definitions and conventions

Metric signature is (−+++). Physical proper-time rates H and σ have units s⁻¹; A is physical acceleration in m s⁻². In intermediate covariant equations use unit timelike u with u·u=−1 and proper length s=cτ, so the physical acceleration is c² u·∇u. No hbar or k_B is suppressed in a thermodynamic response; they do not occur in the following kinematic equations.

The primary HTT object is the typed joint tensor state and its **functional/set/path-valued** reports, as already specified in `HTT_VECTOR_TENSOR_MES_TWO_PILLAR_UPGRADE_PLAN_20260730.md` and `tensor_joint_r9/revision2/MODEL_TO_DATA.md`. The full tuple is not a scalar tuple: x is sample × functional (with each functional's rank/parity preserved); Q is the matching anchor gauge/margin; F separates directional support, sample pushforward and measure-defined occupancy; Pi is an exceedance surface under an explicit law; G_F is a structured functional depth path. Only eligible positive one-dimensional projections use the legacy ratio. The theory below restores these distinctions rather than replacing the user's tensorized research with x_C alone. See T7.

The retained real CMB carrier is orthonormal: c_l0=a_l0, c_lm,c=√2 Re a_lm, c_lm,s=−√2 Im a_lm. Write its STF quadrupole **T₂** and octupole **T₃**, avoiding collision with the anchor score **Q**. Their squared norms are 15||c₂||²/(8π) and 35||c₃||²/(8π), respectively. The following scalar quantities are legacy projections of the richer framework.

The repository's conditional same-congruence quantities remain

\[
x_C=\Sigma_G^2-W_G^2+\Omega_{\rm tilt}+\Delta\Omega_k,
\quad \Sigma_G^2=\frac{\sigma_G:\sigma_G}{6H_G^2},
\quad W_G^2=\frac{\omega_G:\omega_G}{6H_G^2},
\quad Q=\frac{x_C}{U_\sigma},\quad U_\sigma=\frac32 B_\sigma^2>0.
\]

U_sigma is a shear-sector MES normalizer, not a bound on signed x_C. F is defined only on its registered sign-clean, positive-ceiling admissible sector. Pi_Q is strict source-measure exceedance, not a null p-value. Actual production `IsotropyGap.G_F` takes the ratio of floored **bin summaries** (`F_Bayes` is the mean of samplewise fractions in the present unweighted class). It does not average per-draw ratios. A generalized weighted implementation requires its own explicit contract. The independently checked example F_r=(.1,.9), F_c=(.2,.8), delta=.05 gives G_F=1, while mean(F_c/F_r)=13/9.

## T1. Positive kinetic stress gives an algebraic acceleration response

**Premises.** In a smooth energy frame q_a=0 in a neighbourhood, the matter stress tensor is conserved, its energy density epsilon is positive, and its spatial stress is P_ab=p h_ab+pi_ab, with P positive semidefinite. A nonnegative collisionless particle distribution has this positivity since v^a P_ab v^b is an integral of a square with nonnegative weight. We use its moment constraints only; no kinetic hierarchy is evolved. For a conserved species with external forces or a nonzero energy-flux frame, the omitted force/flux terms must instead be included.

The spatial projection of ∇_b T^{ab}=0 gives, with physical units restored,

\[
M_{ab}\frac{A^b}{c^2}=-g_a,
\quad M=(\epsilon+p)I+\pi=\epsilon I+P,
\quad g_a=D_a p+D^b\pi_{ab}.
\]

Thus

\[
\boxed{A=-c^2M^{-1}g,\qquad \|A\|\le \frac{c^2\|g\|}{\epsilon}.}
\]

**Proof.** For every spatial v, vᵀMv=epsilon||v||²+vᵀPv≥epsilon||v||². Therefore M is positive definite, its inverse norm is at most 1/epsilon, and the displayed solution and bound follow. Acceleration has the correct dimension: g/M is inverse length.

For a measured/reference pair (M,g), suppose λ_min(M)≥m>0, ||ΔM||≤eta<m and ||Δg||≤r. The resolvent identity and Weyl's bound give

\[
\|A(M+\Delta M,g+\Delta g)-A(M,g)\|
\le c^2\left[\frac r{m-\eta}+
\frac{\eta\|g\|}{m(m-\eta)}\right].
\]

This is a directly computable response-error bound. It avoids replacing the full matter dynamics with an arbitrary acceleration term. It does not infer pressure gradients from an optical centroid catalogue. It also does not add A² to x_C: the registered Gauss budget and the optical dipole are different equations.

**Literature relation.** Clarkson & Maartens, arXiv:2610.04284v1 (2026 preprint), equations 18, 52, 56–58, give the exact momentum constraint and nonlinear acceleration solution. The positivity argument and perturbation bound here are elementary consequences tailored to an uncertainty contract. The paper distinguishes this exact constraint from a velocity-truncated evolution closure. Its quantities are not the HTT filling F or exceedance Pi, despite overlapping letters.

**Research consequence.** A dipole may reflect an observer boost, intrinsic acceleration of a velocity-dispersed matter congruence, or calibration/selection. A dust/geodesic model is a testable submodel; it must not be an unspoken prerequisite of every solver-free study. Estimating g needs independent tracer/dispersion/gradient information and a tracer-to-matter assumption.

## T2. The local optical quadrupole determines a shear-sector invariant

For one smooth congruence u followed by idealized emitters and the reference observer, a regular optical vertex, no caustic in the local expansion, and locally invertible redshift, let n point toward the source. The local directional redshift-distance coefficient is

\[
\mathcal H_u(n)=H_u-\frac{A_u\cdot n}{c}+\sigma_{u,ab}n^an^b,
\quad d_L(z,n)=\frac{cz}{\mathcal H_u(n)}+O(z^2).
\]

To obtain it, contract ∇_a u_b=−u_a a_b+(H_u/c)h_ab+σ_u,ab/c+ω_u,ab/c with the null direction u−n. The antisymmetric term drops out. Converting proper length to proper time restores H, σ and A/c. A moving observer requires the covariant boost of redshift, distance and angle; changing only redshift does not implement that transformation.

Let h₂(n)=σ_u:nn and let angle brackets denote dOmega/(4π). Since

\[
\langle n_an_bn_cn_d\rangle=
(\delta_{ab}\delta_{cd}+\delta_{ac}\delta_{bd}+\delta_{ad}\delta_{bc})/15,
\]

tracefreeness gives

\[
\boxed{\Sigma_u^2:=\frac{\sigma_u:\sigma_u}{6H_u^2}
=\frac54\left\langle(h_2/H_u)^2\right\rangle,\qquad
\sigma_{u,ab}=\frac{15}{2}\left\langle h_2(n)(n_an_b-\delta_{ab}/3)\right\rangle.}
\]

The fourth-moment coefficient follows by double tracing: its three contractions sum to 15. The quadrupole norm follows by contracting twice with σ. These identities hold on the full sphere, not on an uncorrected selected-sky average. For a mask, fit all retained angular modes using the actual response/design and propagate their joint covariance.

If a simultaneous confidence event supplies ||h₂_hat−h₂||_L2≤r and 0<H_minus≤H_u≤H_plus, the triangle inequality yields

\[
\frac54\frac{(\|\hat h_2\|-r)_+^2}{H_+^2}
\le \Sigma_u^2\le
\frac54\frac{(\|\hat h_2\|+r)^2}{H_-^2}.
\]

Its coverage is inherited from that joint event. The radius must include the finite-z approximation/boost/selection/calibration errors claimed to be covered. A sensitivity parameter r supplies conditional bounds, not measured coverage. With H_minus=0 there is no finite upper quotient bound.

**Connection to x_C.** This is the shear term in x_C only if u is the registered G congruence or a qualified map to it is supplied. It does not supply vorticity, tilt or curvature. A physically justified shear-only estimand can satisfy a separately scoped S04 research objective without waiting for every term of x_C. Actual finite-redshift fit coefficients remain optical effective coefficients until the required local interpretation is established.

Sources: Heinesen (2021), DOI 10.1088/1475-7516/2021/05/008; Maartens et al. (2024), arXiv:2312.09875v3; finite-range caution: Bendtsen et al., arXiv:2608.07008v1. Wolfram angular integration returned identity residual 0; independent finite angular quadrature returned 2.43e−17.

## T3. Tensor orbit distances remain defined on degenerate strata

Let V be a finite direct sum of real STF multipoles, with strictly positive fixed scalar weights per irreducible multipole in its squared norm. The SO(3) action rho is orthogonal for that norm. Define

\[
d_G([v],[w])=\min_{R\in G}\|v-\rho(R)w\|,\qquad G=SO(3)\ \hbox{or}\ O(3).
\]

This is a metric on rotation orbits and obeys

\[
|d_G(v,w)-d_G(v',w')|\le\|v-v'\|+\|w-w'\|.
\]

**Proof.** Compactness of G gives a minimizer. Distance zero means equal orbits. Orthogonality and replacing R by R⁻¹ give symmetry. Composing minimizing rotations and applying the triangle inequality gives the triangle inequality on orbits. Apply the ordinary triangle inequality at one minimizing rotation, then reverse the two pairs, to obtain the Lipschitz bound. Zero tensors, repeated eigenvalues and a singular Krylov chart require no chosen axis and remain valid rows.

This replaces a fragile coordinate chart only for orbit comparison; it does not reconstruct a physical family. SO(3) retains chirality; O(3) deliberately identifies reflections. An arbitrary fixed anisotropic Mahalanobis matrix does **not** make rotations isometries. Simultaneously transforming covariance and data gives coordinate covariance, which by itself does not prove an orbit metric on tensor states alone. The stated theorem uses the invariant tensor norm and propagates anisotropic error sets separately. The legacy high-source/mask aliasing is still part of the error set.

Consequently, uncertainty balls of radii r_v,r_w imply the certified interval

\[
[(d_G(\hat v,\hat w)-r_v-r_w)_+,\ d_G(\hat v,\hat w)+r_v+r_w].
\]

A local optimizer supplies a feasible upper bound on d_G, not a certified lower bound. A scalar lower bound is | ||v||−||w|| |; stronger certified optimization is optional if a decision requires it. Our numerical example verifies an exactly solvable scaled-rotation case, not a general SO(3) optimizer. Primary context: Land & Magueijo (2005), DOI 10.1111/j.1745-3933.2005.00065.x; retained HTT tensor synthesis 20260903.

## T4. Full latent source identification is stronger than functional inference

For an observation map O and a source class P, a target h(P) is identified precisely when it is constant on each fibre {P:O(P)=nu}. Otherwise retain its set of possible values. This is the standard identification criterion, not a new no-go theorem.

A simultaneous set C(D) with P_v(v∈C)≥1−alpha immediately gives coverage for every registered functional through [inf_C h,sup_C h]. This includes the nonlinear shear bound above, signed x_C, Q, admissible F, and production G_F. The set must cover the actual selected experiment; conditioning on a selection made from noisy outcomes can invalidate an unconditional interval.

For nonnegative retained source weights with sum_i p_i=1−u, 0≤u≤1, and simultaneous closed intervals q_i∈[l_i,r_i], with unknown source mass u,

\[
\sum_i p_i1[l_i>t]\le\Pi_Q(t)\le u+\sum_i p_i1[r_i>t].
\]

The same joint confidence event makes these bounds simultaneous over all t. Strict ties remain strict. Joint optimization can tighten a rectangular bound. If u=1, the physical interval stays [0,1]; new optical intervals do not fill it. A posterior pushforward requires a posterior source; a confidence-set image does not become a posterior by normalization.

For G_F use the joint image of bin-summary F values. Independently pairing bin draws discards their coupling. For 0<delta≤1, g(a,b)=max(a,delta)/max(b,delta), a,b∈[0,1], satisfies

\[
|g(a,b)-g(a',b')|\le |a-a'|/\delta+|b-b'|/\delta^2.
\]

The fixed floor makes the map continuous but can amplify uncertainty when very small. Undefined F is not a zero to be floored.

The selection appendix additionally derives sharp selection-odds event/quantile bounds, verifies them against 180 finite LPs, and proves the exact transported-mean bias decomposition. Its selection weights and physical posterior weights are separate objects. The full 628-frame bounded-response missingness width is 354/628=0.5636942675; 274/628 is not a measured propensity function.

## T5. A nuisance envelope can replace a complete generator for a narrower test

Berger–Boos (1994) supplies the established construction

\[
p_{BB}=\min(1,\sup_{\eta\in C_{1-\gamma}(D)}p_\eta(D)+\gamma).
\]

Assume each p_eta is valid at its fixed nuisance value and the set covers the true nuisance with probability at least 1−gamma. For gamma≤alpha<1, rejection on the covered event implies p_true≤alpha−gamma; adding the uncovered probability gives rejection probability≤alpha. Independence between the two ingredients is not required. For alpha<gamma rejection is impossible; alpha=1 is trivial. A numerical maximum over a coarse grid can underestimate the supremum and is not a valid conservative certificate.

For a linear contrast with an admissible mean-bias interval [b_minus,b_plus] and Gaussian standard error s, a simple valid interval is [estimate−b_plus−z*s, estimate−b_minus+z*s]. This recovers the existing quotient/support-function approach and therefore should be reused, not presented as a newly solved blocker. The new task is to obtain and compare justified nuisance sets, or explicitly report sensitivity to their radii.

For Planck splits d_s=c+f_common+f_s+n_s, any split contrast D with D1=0 annihilates both c and f_common. This exact linear kernel shows why tiny split differences do not constrain common foreground contamination. Use frequency response, bounded templates, external comparison and matched processing to constrain common modes. Cross-spectra require the cross-noise term; they do not remove common foregrounds. No claim that PR3 HM FFP10 CMB suddenly exists is made.

Sources: Berger & Boos, DOI 10.1080/01621459.1994.10476836; Armstrong & Kolesár, DOI 10.3982/QE1609; Planck 2018 IV/VIII; Sheehy & Slosar, arXiv:1709.09729. A narrower valid test would be a new observational result, not reproduction of the missing original H02/L03 generator.

## T6. Valid-domain power must accompany response rank

Consider the retained K03 **working Gaussian experiment** a_hat_b∼N(a_b,C_bb), after profiling the local-velocity and finite nuisance columns. Here a_b=K_H b, K_H=14.76646685987891 microarcsec/year and R=7499.25. Restrict the illustrative compensation domain to R||b||≤epsilon. This restriction is necessary for the old linearization to be small; epsilon alone is not a certificate for every neglected remainder.

The maximum allowed squared Mahalanobis shift is

\[
\boxed{d_{\max}^2=(K_H\epsilon/R)^2\lambda_{\max}(C_{bb}^{-1}).}
\]

**Proof.** The norm constraint is a Euclidean ball in a_b. Maximizing its quadratic form aligns it with the largest eigenvector of the information matrix. The top-left covariance of the full six-parameter fit equals the inverse Schur information for the history parameter, so local-velocity nuisance is correctly profiled rather than fixed.

For testing zero mean against any specified allowed alternative, the Neyman–Pearson Gaussian test has power Phi(Phi⁻¹(alpha)+d). Thus any level-alpha test in this Gaussian mean experiment has power at most

\[
\Phi(\Phi^{-1}(\alpha)+d_{\max}).
\]

The comparison is an oracle upper bound; a composite alternative cannot gain power above its best simple-direction test. It concerns this fixed summary experiment, not every future observable, covariance or cosmology.

The actual retained covariance eigenvalues are (0.66318961,0.69679078,0.87889887) (microarcsec/year)². For epsilon=.1, d_max=0.00024179087493 and the level-.05 power upper bound is **0.050024942216**. At epsilon=.01 and .3 the bounds are 0.050002493775 and 0.050074856412. Even the best direction in the declared small domain is almost indistinguishable from zero under this working covariance.

This is new numerical information from the retained source summary, with no catalogue replay. It explains why well-conditioned rank6 did not advance the physical target. More full-row passes at the same response and covariance will not change these numbers. A different source law, better information, a different observable or a distinct physical parameterization would define a new experiment. Unknown spatial covariance and photocentre response remain unqualified, so this is not an empirical physical upper limit or universal impossibility claim.

## T7. A tensor-functional confidence bundle retains the original research object

This section reuses and sharpens the existing July tensor plan and R9 revision 2. These are established convex/geometric/statistical facts applied to HTT, not claims of new mathematical priority. The scalar x_C and bin-ratio example above are projections, not replacements for this bundle.

**Joint domain.** Let Z contain the typed physical/observable tensor state, shared nuisance eta, anchors A, and every response/remainder variable used by the target. Store frame, congruence, epoch/window, scale, units, parity and response identity. Let C(D) be one simultaneous confidence region for this Z. A physical component absent from the qualified observation map remains an unrestricted or explicitly restricted coordinate; zero filling is forbidden. For every eligible registered functional phi, retain K_phi(D)=phi(C(D)) as a set, or a certified outer set, with empty/unbounded/undefined/unresolved distinct.

**Simultaneous image theorem.** On the single event Z_true∈C(D), phi(Z_true)∈K_phi(D) for every phi, every depth and every direction. Hence this family of images inherits coverage at least 1−alpha from C without an extra Bonferroni penalty for merely inspecting deterministic images. This does not authorize post-hoc selective confidence regions, new data-dependent tests, or independent jet intervals outside the covered coordinates. An extra 95% region is not automatically part of the same 95% event. Multiple products require joint construction or prospective error allocation and intersection in the **shared state** before projection, not independence of separately projected marginals.

**Gauge stability.** In a finite-dimensional normed tensor space, suppose A is a closed convex balanced body, rB⊂A⊂RB with 0<r≤R<∞. Define gamma_A(v)=inf{t≥0:v∈tA}. Convexity/balancedness gives a norm and the triangle inequality; the inner ball implies

\[
|\gamma_A(v)-\gamma_A(w)|\le\gamma_A(v-w)\le\|v-w\|/r.
\]

If an uncertain matching anchor obeys (1−eta)A⊂A'⊂(1+eta)A, 0≤eta<1, then inclusion reverses gauges:

\[
\frac{\gamma_A(v)}{1+\eta}\le\gamma_{A'}(v)\le
\frac{\gamma_A(v)}{1-\eta}.
\]

Combining state error ||v−vhat||≤delta and anchor containment gives lower max(0,gamma_A(vhat)−delta/r)/(1+eta) and upper (gamma_A(vhat)+delta/r)/(1−eta). These are deterministic outer bounds; coverage requires these premises on the same confidence event. For a non-balanced body gamma need not be symmetric: replace the norm-difference bound by the corresponding one-sided gauges. NO_MES_ANCHOR is not r=0 followed by division. If an equivariant frame rotation acts on both state and anchor, gamma_{rho(R)A}(rho(R)v)=gamma_A(v), directly by the membership definition. Rotating the state alone with a fixed anisotropic anchor changes the question.

**Directional support and F.** For a nonempty compact set K define h_K(u)=sup_{v∈K}<u,v>. If K and L are nonempty compact convex sets in a Euclidean tensor representation,

\[
d_H(K,L)=\sup_{\|u\|=1}|h_K(u)-h_L(u)|.
\]

Proof: K⊂L+delta B and L⊂K+delta B imply the support inequalities. Conversely those inequalities imply these inclusions by separation of closed convex sets. For nonconvex K, support sees only conv(K), so no claim of reconstructing disconnected or chiral strata follows. Preserve the actual set/strata separately.

Where a matching anchor has h_A(u)>0, the typed support-utilization profile F_sup(u)=h_K(u)/h_A(u) is defined. Signed directional values are not occupancy probabilities. With fixed A containing rB and d_H(K,L)≤delta, |F_sup,K(u)−F_sup,L(u)|≤delta/r for unit u. If K⊂MB then h_K is M-Lipschitz in u; an epsilon-net gives max_grid h_K≤sup_unit h_K≤max_grid h_K+M epsilon. For support differences use M_K+M_L. Therefore finite directional search can acquire a certified upper correction when a radius bound exists; without it a grid maximum is only a lower bound. For F_sup the same correction must also propagate the anchor denominator; do not reuse the support-only correction unchanged.

The current `common/tensor_functionals.py` already evaluates fixed-contraction fibres. For full-row-rank L, L o=v, ||o||=1, let o0=L^dagger v, eta0=||o0||² and Pker be the orthogonal kernel projector. When eta0≤1 and the relevant kernel sphere is nonempty,

\[
h(u)=u\cdot o_0+\sqrt{1-\eta_0}\,\|P_{\ker L}u\|.
\]

This follows from the orthogonal decomposition o=o0+w and Cauchy–Schwarz, with equality in the kernel direction. Current 3×7 full-row-rank fibres have nonzero kernel. The equality-boundary singleton must be distinguished from an empty fibre and numerical ambiguity. The code labels its numerical result NUMERICALLY_CHECKED_FIXED_FIBRE, refuses uncertain q, and is not a confidence-set certificate. For uncertain quadrupole q, optimize over the **joint** q/v region with certified outer inclusion; inserting qhat discards its uncertainty and generally changes the identified set.

**Pi surfaces.** Let mu be an explicitly named source/posterior/null law. For an eligible score q_phi define Pi_mu(phi,t)=mu{q_phi>t}; it is not generically a p-value. If weighted finite samples have simultaneous lower/upper score bounds across phi, T4 gives simultaneous outer surfaces over (phi,t). A confidence set without a probability law supplies score/support sets, not a fabricated mu. Unknown physical mass remains unknown even when optical morphology is estimated accurately.

**Information-preserving depth path.** Stack Y=(Y0,...,Ym). Let T map it to Z_depth=(Y0,Y1−Y0,...,Ym−Y_{m−1}). T is invertible, with Yk=Y0+sum_{j≤k}DeltaYj. In a Gaussian working experiment, transform mean and the **entire** covariance: C_Z=T C_Y T^T. For nonsingular C_Y the quadratic likelihood form and Fisher information are unchanged because T is invertible; the determinant factor is parameter-independent. Singular laws require transformation of the support as well. Differences alone annihilate every common-depth vector and cannot identify its level. Adjacent differences share covariance even when original bins were independent.

Thus G_F is a `FunctionalDepthPath`: raw tensors, gauge/support profiles, shared covariance and windows along depth. Signed/zero-crossing paths use differences or set paths. The legacy floored ratio is available only in the positive eligible one-dimensional projection, and is not global-tilt evidence by itself. A morphology depth trend can be studied without solving cosmological histories, but attribution of that trend to global tilt still needs the physical response. This is precisely the independence principle already present in R9 revision 2.

**Executed checks.** `analysis.py` now additionally checks ellipsoidal gauge equivariance and perturbation containment, exact ball support/Hausdorff equality, the existing fixed-fibre formula against a constructed witness, and full-covariance depth-likelihood/Fisher invariance. These validate finite examples of the derivations, not observational coverage or all optimization strata.

## R1–R10 execution and independent obligations

R1 fixed solver-free scope and original counts; R2 read pinned current and legacy definitions plus primary papers; R3 separated optical, tensor, physical and probabilistic objects; R4 constructed narrow estimands and alternative methods; R5 supplied the proofs above; R6/R7 checked angular algebra with Wolfram and independent numerical quadrature, Schur information and finite examples; R8 retained conditional scope and historical failures; R9 supplies executable `analysis.py`, source extraction, figure and action DAG; R10 supplies a copyable continuation prompt without resetting the existing 48-task state. Independent candidate review is recorded separately in `REVIEW.json`.

The old 628/274 residual failure (T=4.5553218238,p=.0009763241396), 97 LPs, D07 endpoint crossings, physical unknown mass1, absent original external V03 and full B02 atlas remain recorded as they were. The useful next experiment is model comparison on the same selected source and finite domain, not a renamed replay of those failed claims.
