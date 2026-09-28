# MES-normalized tensor statistics for all kinematical sectors

Candidate-author note for the fresh R2 loop. Evidence status: **derived** for the stated finite-dimensional propositions; **numerically checked** only for the synthetic algebra in `statistics_checks.json`. No astrophysical data were fitted, no evolution equation was integrated, and no repository prior research was used. The local R1 report was read only for the previously declared meanings of `x,Q,Pi,F,G_F`. This note is not an independent decision gate.

## 1. Constructive target

The intended comparison can be made precise without identifying shear and vorticity as the same tensor. Use a rank-graded tensor bundle, a common observational experiment, and a declared admissible body. Its radial gauge measures a fraction of the permitted amplitude in the observed direction. The original percentage is then exactly `100(1 − fraction)`. Retain the normalized tensor alongside this scalar, so that morphology is never reconstructed from the percentage.

There are two different, compatible meanings of fairness:

1. **Physical-budget fairness:** the same fraction of each sector's declared MES budget, under the same data, frame, redshift, nuisance conventions and assumption set.
2. **Statistical fairness:** the same null-calibrated tail probability or likelihood loss, accounting for the number of measured components and their covariance.

The first is the user's original objective. The second is a necessary companion when results are described as equally significant. Neither requires that different-rank tensors be subtracted from one another.

## 2. The tensor bundle and physical units

Fix one physical congruence `u`, one orthonormal observer frame, metric signature `(-,+,+,+)`, and an expansion scale `H_* > 0` in s^-1. Form

\[
k(z)=\left(\delta\theta/H_*,\;\sigma_{ab}/H_*,\;\omega_a/H_*,\;
A_a/(cH_*),\;\beta_a\right)
\in E=\mathbb R\oplus\mathrm{STF}^2\oplus V_{\rm axial}\oplus V_{\rm polar}\oplus V_{\rm polar}.
\]

The dimensions are `1 + 5 + 3 + 3 + 3 = 15`; there is an extra sector label even when two components have the same tensor rank. Under reflections vorticity is axial, whereas acceleration and velocity are polar. `theta,sigma,omega` have physical rate units s^-1, `A` has m s^-2, and `beta=v/c` is dimensionless. If local observer boost and global fluid tilt are both unknown, give them separate 3-vector slots, reference congruences and response columns; do not identify them by notation.

Here `delta theta = theta − theta_ref` is explicit. Dividing theta by `H=theta/3` produces the identity 3 and supplies no observational expansion constraint. Absolute theta or delta theta requires a dimensional anchor and an applicable inequality. No numerical MES coefficient or acceleration/tilt theorem is invented here: the source audit must supply the actual target, normalization and assumptions for each denominator. A causal speed limit `|beta|<1` is not a MES observational bound.

For multiple depths, use a finite collection `E(z_i)` with a declared transport map between frames, or coefficients of a stated radial basis with a controlled truncation remainder. An observed CMB last-scattering map is not itself a sequence of independently observed local kinematic epochs.

## 3. A common body gives a common percentage

Let `B(chi)` be a certified outer allowed body for `k−k_ref` in this dimensionless bundle. `chi` contains true radiation moments, derivative/source budgets, frame and redshift assumptions, and any finite-order remainder. A bound need not be sharp or physically attainable. Therefore its boundary is an **allowed/reference boundary**, not necessarily `k_max` of a realized spacetime.

Assume for this construction that B is bounded, closed, convex and contains the origin in its interior. Convexity is convenient, not essential: a star-shaped body with a positive finite radial function suffices for radial normalization. A convex hull used in place of the physical feasible set must be labelled an outer approximation.

Define the Minkowski gauge

\[
\gamma_B(y)=\inf\{\lambda>0:y\in\lambda B\},\qquad y=k-k_{\rm ref}.
\]

Then `gamma_B(y)<=1` if and only if `y in B`, and `gamma_B(alpha y)=alpha gamma_B(y)` for alpha>=0. For the Frobenius ball `B_s={y_s:||y_s||<=b_s}`,

\[
\gamma_{B_s}(y_s)=\frac{\|y_s\|}{b_s},\qquad
D_s=100\left(1-\frac{\|y_s\|}{b_s}\right).
\]

Thus the intended `1 − observed / MES bound` is recovered exactly for an amplitude comparison. `D=100` means zero displacement from the declared reference, `D=0` means saturation of the declared bound, and `D<0` means that the inferred displacement lies outside that bound. It is neither a probability nor a fraction of spacetime that is FLRW. A bound-violating best fit can reflect noise, source contamination, frame error, approximation failure or failure of the assumptions; the likelihood determines which alternatives the data support.

If all that is known is a list of separate bounds, the joint outer body is the product

\[
B_{\rm product}=\prod_s B_s,\qquad
\gamma_{B_{\rm product}}(y)=\max_s\gamma_{B_s}(y_s).
\]

One may report every component fraction as well as this joint worst fraction. Replacing the maximum by a sum of squares would invent a stronger joint constraint. For fractions `(0.8,0.8)`, the product admits the state whereas an independent unit ellipsoid has gauge `sqrt(1.28)=1.13137` and excludes it. Conversely, genuinely coupled MES/field-equation constraints should be retained in B instead of being discarded after taking marginal suprema.

If a direction is unbounded, its gauge can vanish for a nonzero vector. That must not be advertised as 100% agreement. Restrict the percentage to a declared bounded controlled subspace and report the remaining sector as uncontrolled. If a bound is zero, the associated sector is forced to zero under the assumptions but its 0/0 percentage is undefined. If a bound is merely a leading-order estimate, write `B_reference` and do not assert exact confinement to `[0,1]` without a remainder bound.

## 4. Morphology-preserving normalization theorem

Choose a positive rotation-invariant inner product G on E. Sector units and multiplicity weights are declared, not fitted after seeing the result. For unit u let

\[
\rho_B(u)=\sup\{r\ge0:ru\in B\}.
\]

Define

\[
\boxed{T_B(y)=\begin{cases}
\dfrac{y}{\rho_B(y/\|y\|_G)},&y\ne0,\\
0,&y=0.
\end{cases}}
\]

Since `gamma_B(y)=||y||_G/rho_B(y/||y||_G)`,

\[
\boxed{\|T_B(y)\|_G=\gamma_B(y)},\qquad
y=\rho_B(T/\|T\|_G)\,T\quad(T\ne0).
\]

Consequently this map retains every directional/morphological degree of freedom and maps B onto the unit ball. It is not the only useful normalization. For an ellipsoid `B={y:y^T W y<=1}`, `T=W^(1/2)y` is linear and has the same norm/gauge, but it whitens the physical shape; retain W and the unwhitened tensor if principal axes have physical meaning.

For a spatial rotation R acting in all tensor representations, rotate the *body as well as the data*. Because G is rotation invariant,

\[
T_{RB}(Ry)=R\,T_B(y).
\]

This is the desired tensor covariance. Holding an anisotropic mask-derived or response-derived B fixed while rotating only the sky is a different experiment. Arbitrary coordinate/component changes also transform the metric and body. No scalar percentage uniquely fixes the cross-sector metric; the sector-resolved fractions remain interpretable without that choice.

The scalar budget occupancy and deviation are

\[
F_B=\|T_B\|_G^2=\gamma_B^2,\qquad
D_B=100(1-\sqrt{F_B}).
\]

Using `100(1−F_B)` instead gives a **quadratic-budget** deficit, not the amplitude deficit requested by the user. Neither should silently replace the other.

For **sector-to-sector comparison**, also retain the marginal/sector maps `T_s=T_{B_s}(y_s)` and their fractions `||T_s||=gamma_{B_s}(y_s)`. The direct sum of these separately normalized tensors is a useful representation, but its squared norm is generally not the joint gauge squared. Conversely, an individual block norm of the *joint* radial tensor `T_B` need not equal that sector's own bound fraction. Keep the sector scores and the joint-body score separately labelled. This distinction prevents a sector's apparent percentage from changing merely because another sector has been appended to the bundle.

## 5. A tensor completion of Q, F, Pi and G_F

This is a new candidate completion, with symbols distinguished from an unverified exact extension of the historical multi-sector x.

The rank-one positive operator

\[
\mathbb Q=T\otimes_G T,\qquad \operatorname{tr}_G\mathbb Q=F_B
\]

has blocks `T^(s)_{A_n} T^(t)_{B_m}` with ranks `n+m` and the corresponding parity. It retains orientation and cross-sector alignment. It loses the simultaneous sign `T -> −T`; hence always retain T. For the admitted nonnegative unit-budget sector call the same object `mathbb F`, with scalar trace `F_B in [0,1]`. Outside that admission it is a normalized quadratic diagnostic and can exceed 1.

For a joint posterior or a specified repeated-sampling law define, for q>=0,

\[
\boxed{\mathbb\Pi(q)=
\mathbb E\left[\frac{T\otimes_G T}{F_B}\,
\mathbf1_{\{F_B>q\}}\right]},
\qquad
\boxed{\operatorname{tr}_G\mathbb\Pi(q)=\Pr(F_B>q)}.
\]

Set the integrand to zero at `F_B=0`. The indicator then removes the zero case for q>=0. Proof: the trace of the orientation projector is 1 whenever F_B>0. This construction exactly recovers the scalar tail probability, while its tensor blocks show which orientations and sectors contribute to the tail. Unlike an unnormalized weighted tail moment, its trace is a probability. Credible regions for T and tail tensors must still reflect the actual non-Gaussian posterior.

For two epochs/depths, let R be a predeclared isometric transport between their representations in the same G metric, and F_b>0. Define

\[
\boxed{\mathbb G_{ab}=\frac{T_a\otimes_G (R T_b)}{F_b}},\qquad
\boxed{\|\mathbb G_{ab}\|_{\rm HS,G}^2=\frac{F_a}{F_b}=G_F}.
\]

Its trace is `sqrt(G_F) cos(angle)`, so it retains information lost by a scalar growth ratio. Report also `Delta T=T_a−R T_b`. There is no canonical tensor division, and a non-isometric transfer must carry its metric conversion explicitly. Near F_b=0, a ratio distribution can have unstable or nonexistent moments; report the joint `(F_a,F_b)` distribution and do not invent a finite mean growth rate.

### Historical x compatibility

The local R1 note records `x=Sigma_std^2−W_std^2+Omega_tilt+Omega_k,aniso`, `Q=N(x)/U`, `Pi(q)=P(Q>q)`, `F=x/U` in a nonnegative admitted sector, and `G_F=F_a/F_b`. The present `F_B` agrees exactly with that shear-sector F when the shear normalization is `x_sigma=tr(Sigma^2)/6`, `U_sigma=(3/2)B_sigma^2`, and `B_sigma` bounds `||sigma||/theta` with `theta=3H>0`.

For the full signed x this equivalence does **not** follow automatically. Preserve the declared scalar functional `x=X(k,chi)` and its numerator policy N; if its registered components are quadratic, store their contraction operator J so that `x=<k,Jk>_G` plus any explicitly nonquadratic/auxiliary terms. Negative vorticity and signed curvature permit cancellations; `x=0` can hold for a nonzero, highly structured tensor bundle. Therefore x cannot serve as a positive norm or a Minkowski gauge on the full space. `Omega_tilt` need not equal `|beta|^2`, and curvature is an auxiliary sector absent from the five requested kinematic groups. The positive budget geometry and the signed physical invariant can coexist as different contractions of the same joint posterior. Exact full historical equivalence remains unresolved until the original component definitions are supplied in the allowed scope.

## 6. What is actually inferred from a common experiment

Let d contain the measured harmonic coefficients `a_lm^X` for X=T,E,B, any cross-field/bipolar coefficients, redshift-bin data, boost observables, distance-redshift information and instrument calibration actually available. Keep masks, beams and correlated noise. The `C_l` are rotational invariants and cannot on their own encode multipole axes or phase morphology.

In a locally valid finite-basis response model write

\[
d=\mu_0+Rk+N\eta+\epsilon,\qquad\epsilon\sim\mathcal N(0,C),\quad C>0.
\]

Here R follows from covariant optical/moment identities, controlled finite radial expansions, or analytic integral response kernels; it is not obtained by declaring `sigma_observed(C_l)` to exist. N contains declared source/calibration/nuisance columns, and physical remainder bounds are represented separately or as an explicit distribution. This linear model has a stated validity range; a nonlinear forward likelihood is preferable where it is needed and available.

With unconstrained linear nuisance coefficients profiled out,

\[
P=C^{-1}-C^{-1}N(N^TC^{-1}N)^+N^TC^{-1},\qquad
\mathcal I=R^TPR.
\]

The identifiable subspace is `I=range(mathcal I)`. With Moore–Penrose inverse defined in the declared metric/component coordinates,

\[
\hat k_I=\mathcal I^+R^TP(d-\mu_0),\qquad
\mathbb E[\hat k_I]=\Pi_I k,\qquad
\operatorname{Cov}(\hat k_I)=\mathcal I^+.
\]

Proof: `P C P=P`; therefore covariance is `I^+ R^T P C P R I^+=I^+`, and the mean is `I^+ I k`. This is an identifiable tensor combination, not necessarily all physical components separately. Give null vectors and singular values along with the estimator. Finite priors can regularize null directions but do not change which combinations the experiment measured.

The appropriate bound body for this estimate is

\[
\boxed{B_I=\Pi_I B,\quad\hbox{not}\quad B\cap I.}
\]

Projection marginalizes the possible unmeasured components. Intersecting with I forces those components to zero and can spuriously strengthen a constraint. The valid observed statistic is then

\[
\boxed{T_{A_n}^{(s)}(d,z;\chi)
=\big[T_{B_I(\chi)}(\hat k_I(d,z)-\Pi_I k_{\rm ref})\big]^{(s)}_{A_n}.}
\]

If the experiment does not distinguish a velocity-like vector from an acceleration/source-dipole response, this tensor represents the measurable combination. Relabelling it as separate acceleration, local boost and global tilt would exceed the likelihood's rank. Additional depths, polarization, aberration, distances or time-domain information can add linearly independent columns; that is a concrete experimental discriminator.

## 7. Likelihood, same-data denominators and theoretical comparison

The primary likelihood should remain in the observed d space:

\[
-2\log L(k,\eta;d)=
(d-\mu(k,\eta))^T C^{-1}(d-\mu(k,\eta))+\log\det C+\text{constant}.
\]

If C depends on parameters its determinant and derivatives must be retained. `T_theory` and `T_observed` are compared with their full pushed-forward probability law, or as a justified local Gaussian approximation with transformed covariance. For fixed B and an invertible change `t=g(d)`,

\[
p_T(t|k)=p_d(g^{-1}(t)|k)\,|\det Dg^{-1}(t)|.
\]

A many-to-one summary needs its induced sampling law, not this square-Jacobian formula. Using the transformed residual with the old covariance would change the statistical experiment.

If the denominator is inferred from the same sky, it is correlated with the numerator. This is allowed but must be propagated jointly. In the elementary case `r=s/b`,

\[
\operatorname{Var}(r)\simeq
\frac{\operatorname{Var}(s)}{b^2}
+\frac{s^2\operatorname{Var}(b)}{b^4}
-\frac{2s\operatorname{Cov}(s,b)}{b^3}.
\]

If `(r,b)` is retained instead of `(s,b)`, the exact density is `p(r,b)=p(s=rb,b)|b|`. A same-data bound `b=a s` makes r=1/a identically and contains no amplitude information, even though it may remain a useful normalization convention. Data-dependent B requires the joint latent sky/source likelihood or an appropriate conditional sampling law; freezing the observed B and pretending it was externally fixed can misstate uncertainty. If the true MES inputs are uniform all-observer derivative envelopes, the observed single-sky estimates do not automatically supply them.

A bound is a set-valued theory, not a predicted tensor. There are two legitimate tasks:

* **Conditional estimation:** assume `k−k_ref in B` and infer its normalized location. Then `P(k−k_ref outside B | d)=0` is true by construction and is not evidence validating MES. The allowed physical-state body is `k_ref+B`.
* **Assumption/bound checking:** infer in an encompassing model, or compare a restricted fit to an unrestricted fit,

\[
\Delta\chi^2_B=
\min_{k-k_{\rm ref}\in B,\eta}\chi^2(k,\eta)
-\min_{k,\eta}\chi^2(k,\eta).
\]

This measures distance of the likelihood-supported state to the allowed body. Its null distribution depends on boundaries, nuisance variables and identifiability; generic Wilks/chi-square claims are not automatic. A declared composite-null simulation, worst-case tail calibration, or analytic cone result is needed. A Bayesian comparison additionally specifies proper priors for both models. A unique `T_theory` requires a sharper physical hypothesis within B; the MES inequality by itself supplies only the allowed set.

## 8. Rank-fair calibration and a constructive synthetic example

Suppose, purely as an algebraic example, that all five shear components and all three vorticity components are measured with independent Gaussian standard deviation 0.2 in their respective unit-MES coordinates. Compare states of amplitude 0.6 in each sector.

Both have `gamma=0.6`, `F=0.36`, and **40% amplitude deficit from the declared bound**, precisely the desired type-independent physical-budget comparison. Both have standardized squared norm 9. Under a zero-sector null the corresponding tails are nevertheless

\[
P(\chi^2_3\ge9)=0.0292908865,\qquad
P(\chi^2_5\ge9)=0.1090641579.
\]

Thus equal budget fraction is not equal evidence against the zero-sector hypothesis. Report both, without allowing the statistical calibration to replace the physical meaning of the percentage. With masking/correlations/nuisance projection use the actual identifiable rank and the actual null law; nonlinear/data-dependent normalization can invalidate the simple chi-square example.

Morphology also survives: two unit-Frobenius STF directions

\[
E_1=\operatorname{diag}(1,-1,0)/\sqrt2,
\qquad E_2=\operatorname{diag}(2,-1,-1)/\sqrt6
\]

give `T=0.6 E_i` with the same F and D. Their shape invariant

\[
\chi_\sigma=\sqrt6\,\frac{\operatorname{tr}T^3}{(\operatorname{tr}T^2)^{3/2}}
\]

is respectively 0 and 1. The normalized tensors and their tensor quadratic blocks preserve this difference. Relative axes are additionally retained if the observer frame is physically fixed; orientation is undefined at zero amplitude.

The attached finite calculation also verifies nuisance rank loss, an exact null response, the projected-body construction, the tensor-tail trace identity and the tensor-growth Hilbert–Schmidt identity. These are synthetic validation of the proposed mathematics, not measurements or proof that any particular response R describes the actual CMB.

## 9. Research-ready outcome and next decisive calculation

The viable result is a two-layer tool: a common conditional MES budget geometry and a full likelihood for observable tensor combinations. It accommodates every requested rank without a Bianchi-class choice. It does not pretend that a single CMB sky identifies every congruence derivative or that gauge/normalization creates new information.

The smallest next physical calculation is to build an explicit response matrix from the class-independent local optical/redshift and radiation-moment identities, including separate columns for theta, sigma, omega, A, observer boost, global tilt and declared source moments. Determine its nuisance-projected rank before proposing separate posterior estimates. Then attach only the MES bound rows actually verified from allowed sources, retain the projected joint body, and calculate `T,Q,F,Pi,G_F` for a bounded synthetic fixture. This produces a useful tool and a falsifiable identifiability map without running an Einstein–Boltzmann evolution solver.

No public novelty claim, real-data claim, observational percentage, full historical-x equivalence, or unconditional generalization of MES is made in this work unit.
