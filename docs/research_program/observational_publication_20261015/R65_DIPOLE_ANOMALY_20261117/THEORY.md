# R65 — conditional declination quotient and the signed five-view carrier

Bounded theory construction, 2026-11-17. Parent-reported baseline
`d76ef3a4e9b33c4703a02647b3aa850004d04253`, branch
`research/r65-dipole-anomaly-20261117`. Requested skill runtime
`gpt-6-astra/xhigh`; observed runtime identity UNKNOWN. This lane has performed
derivations and read the existing source maps; it has not fitted data, executed
verification, downloaded catalogues, mutated the remote repository, or spawned
children. The root owns actual execution, integration, preservation and publishing.

Skill context: PhysMath Research Loop 1.3.0, POLICY_INTEGRATION and the R4/R5/R9
construction contracts. Canonical five-view semantics were read from
`r63_five_variable_map.md`; source and novelty qualifications were read from
`r65_history.md` and `r65_literature.md`. The latter contain primary-source reading
by the parent literature lane, not independent primary-source retrieval here.

## 1. Observable, units and finite experiment

Use sourceward ICRS unit vectors
`n=(cos(delta)cos(alpha),cos(delta)sin(alpha),sin(delta))`, with Cartesian z along
the equatorial north pole. Dipole coefficients `u,d,beta=v/c` are dimensionless;
retain `c=299792.458 km/s` when reporting velocities. There is no spacetime metric
operation in this Euclidean angular experiment; the parent physical convention is
`(-,+,+,+)`. Flux-bin boundaries refer to the actual NVSS `PEAK INT` column in
**Jy/beam**. They are not measured integrated Stokes-I flux densities in Jy.

For each disjoint, prespecified peak-intensity bin b and HEALPix RING ring r,
let `N_brp` denote source counts in retained pixel p, and let `E_brp>=0` be the
known relative exposure. An exposure of zero excludes a pixel; a positive observed
count in a zero-exposure pixel is an incompatible input, not a numerical zero.
Use precisely the same mask, coordinate centres, bin edges and source membership
in the count and expectation operations. Bin boundaries must be disjoint, for
example `[S_b,S_(b+1))` with an explicitly closed final endpoint if required.

Define `t_rp=(n_x,n_y)` and `z_r=n_z` at the pixel centre. The working law is

\[
 N_{brp}\ \mathrel{\perp}\ N_{b'r'p'}\mid\lambda,\qquad
 N_{brp}\sim\operatorname{Poisson}(\lambda_{brp}),\qquad
 \lambda_{brp}=A_{br}E_{brp}
       \exp\{u_{b\perp}\cdot t_{rp}+u_{bz}z_r\},\quad A_{br}>0.
\]

The coefficients `A_br` are arbitrary ring amplitudes **for each bin**. They
absorb all ring-constant multiplicative completeness and density modes. Restricting
their freedom to a common function across bins is a different experiment that may
retain extra information and requires an additional scientific justification.
The nuisance model protects against declination-only multiplicative distortions;
it does not protect against RA-dependent calibration, an incorrect nonfactorizable
exposure map, source blending, or stochastic clustering.

**Discretization boundary.** HEALPix pixel centres have constant z within a RING
ring. Real source positions in a finite-width ring do not. Nor is
`integral_pixel E(n) exp(u.n) dOmega` generally equal to a scalar exposure times
`exp(u.n_centre)`. Thus the quotient proved below is exact for the declared
pixel-centre model. Replacing the centres by actual source z values, or claiming
an exact continuum result for finite-width pixels, invalidates that proof. If
`||n-n_p||<=h_p`, the log-intensity error from replacing n by its centre is at
most `||u|| h_p`; exposure integration and sharp mask boundaries have their own
errors. A resolution comparison tests this approximation; it does not prove that
unknown true completeness was supplied. If a whole pixel is retained by its
centre, record this mask approximation rather than claiming fractional exposure.

## 2. Exact nuisance quotient in the log-linear model — derived

Write `N_br=sum_p N_brp` and

\[
 Z_{br}(v)=\sum_{p:E_{brp}>0}E_{brp}e^{v\cdot t_{rp}},\qquad
 q_{brp}(v)=\frac{E_{brp}e^{v\cdot t_{rp}}}{Z_{br}(v)}.
\]

Conditioning on all ring totals gives

\[
 (N_{brp})_p\mid N_{br}\sim
 \operatorname{Multinomial}(N_{br},(q_{brp}(u_{b\perp}))_p).
\]

Both `A_br` and `u_bz` cancel exactly. Equivalently,
`u_bz -> u_bz+gamma_b`, `A_br -> A_br exp(-gamma_b z_r)` is an exact
likelihood fibre. This is a theorem about this specified nuisance family and
link function. It is not a universal inability to measure a physical z dipole.

With `T_br=sum_p N_brp t_rp`, omit constants independent of v:

\[
 \ell_b(v)=\sum_r[T_{br}\cdot v-N_{br}\log Z_{br}(v)].
\]

Let `mu_br(v)=sum_p q_brp(v)t_rp` and
`V_br(v)=sum_p q_brp(v)(t_rp-mu_br)(t_rp-mu_br)^T`. Then

\[
 s_b(v)=\sum_r[T_{br}-N_{br}\mu_{br}(v)],\qquad
 -\nabla^2\ell_b(v)=J_b(v)=\sum_rN_{br}V_{br}(v)\succeq0.
\]

Every sign and unit follows from differentiating the log partition function.
At fixed ring totals, `Cov_v[s_b(v)]=J_b(v)` exactly under the multinomial law.
The score has expectation zero under that same law. Empty rings contribute no
likelihood, score or information. Do not divide by their totals.

For any a in R²,

\[
 a^TJ_ba=\sum_rN_{br}\operatorname{Var}_{q_{br}}(a\cdot t)\ge0.
\]

Hence the null space consists precisely of a for which `a.t_rp` is constant on
the positive-exposure support of every positive-count ring. The information rank
is the span dimension of the within-ring direction differences. Arbitrary known
masks are allowed, but full rank is not automatic. Three distinct points on a
nonzero-radius declination circle suffice for rank two; a ring with one exposed
pixel gives no information; two points yield at most rank one; different rings
can jointly supply rank two. This characterization is independent of v at any
finite v because positive exposures retain positive multinomial probabilities.

Concavity makes every finite stationary point a global maximizer, unique in the
identified quotient. A finite maximum need not exist when the observed statistic
lies on the boundary of its convex support. The support for `sum_r T_br` is the
Minkowski sum `sum_r N_br conv{t_rp:E_brp>0}`. Relative-interior membership is the
usual finite-MLE criterion after removing exact null directions. Optimizer success
alone is insufficient: retain score norm, curvature/rank, objective, and finite
parameter checks. Infinite or boundary estimates are an explicit outcome.

## 3. Exact profile equality and what score compression preserves — derived

Absorb z into `eta_br=log A_br+u_bz z_r`. The full Poisson log likelihood for one
ring, apart from constants, is

\[
 \ell_{br}(\eta,v)=N_{br}\eta+T_{br}\cdot v-e^\eta Z_{br}(v).
\]

For `N_br>0`, `exp(eta_hat)=N_br/Z_br(v)`. Substitution gives

\[
 \ell^{\rm prof}_{br}(v)
 =T_{br}\cdot v-N_{br}\log Z_{br}(v)
   +N_{br}\log N_{br}-N_{br},
\]

exactly the conditional likelihood plus a parameter-independent constant. For
an empty ring the supremum is approached at `eta=-infinity`, with zero information.
No finite artificial regularization of the ring amplitude should be added.

If `Lambda_br=sum_p lambda_brp`, the expected full information blocks for
`(v,eta_1,...,eta_R)` obey

\[
 I_{vv}=\sum_r\Lambda_r E_q[tt^T],\quad
 I_{v\eta_r}=\Lambda_r\mu_r,\quad
 I_{\eta_r\eta_s}=\delta_{rs}\Lambda_r.
\]

Their Schur complement is

\[
 I_{v\cdot\eta}=\sum_r\Lambda_r
       (E_q[tt^T]-\mu_r\mu_r^T).
\]

At profiled ring amplitudes `Lambda_r=N_r`, this equals the conditional negative
Hessian. It is also the Fisher expectation of conditional information when
averaged over totals at the true parameters. These are distinct identities;
unconditional expected information at arbitrary A does not equal a realized
conditional Hessian with N substituted without explaining that substitution.

At a fixed reference v0 the retained score

\[
 S_b=\sum_rT_{br}-\sum_rN_{br}\mu_{br}(v_0)
\]

is an affine encoding of the sufficient statistic `sum_r T_br`. Together with
the conditioned totals and known normalizers/supports, it preserves **the whole
conditional exponential-family likelihood**, not just Fisher information.
The exact compression is model-specific: new angular templates require their
own sufficient statistics unless their columns lie in the retained span.
The pair `(v_hat,J(v_hat)^-1)` alone is normally only a local Gaussian carrier;
it cannot reproduce every nonquadratic likelihood ratio. Save the exact
normalizer inputs or a lossless representation of `ell_b(v)` as well.

For a local Gaussian experiment `y~N(X theta+Z eta,C)`, write `C=LL^T`,
`A=L^-1 X`, `B=L^-1 Z`, `P=I-B B^+`, `z=L^-1 y`. Then
`J=A^T P A`, `s=A^T P z` are the nuisance-profile precision and score. This is
the same local information as the ring-centred construction. Whiten the **full**
C before projecting; deleting cross-block covariance changes the experiment.
For any deterministic diagnostic `Y=f(data)`, its score is
`E[score_data | Y]`, so Fisher information cannot increase. Equality requires
the original score to be measurable from Y (under the regularity used in this
identity). An invertible path transform preserves information; a collection of
five scalar norms generally does not.

## 4. Physical linear density is only locally the same model — derived

The physical first-order count-density convention is

\[
 \lambda_{rp}=A_rE_{rp}(1+d_\perp\cdot t_{rp}+d_z z_r),
 \qquad 1+d\cdot n_p>0.
\]

With arbitrary ring amplitudes its exact conditional probabilities are

\[
 q^{\rm lin}_{rp}(d)=
 \frac{E_{rp}[1+w_r(d)\cdot t_{rp}]}
      {\sum_qE_{rq}[1+w_r(d)\cdot t_{rq}]},\qquad
 w_r(d)=\frac{d_\perp}{1+d_z z_r}.
\]

At d=0 the d_z score is exactly zero and the transverse tangent is the same as
the exponential model. Away from zero,
`partial w_r/partial d_z=-z_r d_perp/(1+d_z z_r)^2`, which is generally nonzero.
If `d_perp!=0`, two informative rings with different z can in principle determine
d_z from the differing transverse scale factors. Thus **an all-order physical
d_z no-go would be false**. The extra effect is of order `d_perp d_z` in the
probability expansion and the d_z Fisher information is of order
`N ||d_perp||^2` near a small nonzero transverse dipole. At exactly
`d_perp=0`, d_z remains absent; a single ring also retains an exact scale fibre.
Those counterexamples delimit any positive identifiability statement.

The log-link parameter u is therefore a directly defined count-modulation
parameter, identified with physical d only to first order. The exponential
model includes fixed higher-order angular terms absent from the linear density
model. Neither link is the exact Lorentz-boosted selected population by definition.

A finite bound makes this qualification reproducible. For `|x|<=epsilon<1`,

\[
 |e^x-(1+x)|\le\tfrac12 e^\epsilon\epsilon^2,
 \qquad h(x)=x-\log(1+x)\in[0,H],\quad
 H=-\epsilon-\log(1-\epsilon).
\]

Thus, at the **same** vector `u=d` with `||d||<=epsilon`, the exponential and
linear conditional laws on each ring differ by a bounded exponential tilt h.
Their pointwise log probability ratio has absolute value at most H. Both KL
directions are at most `H^2/8`: for
`f(t)=log E_linear exp(t h)`, use `f''(t)=Var_t(h)<=H^2/4` and integrate either
`f(1)-f'(0)` or `f'(1)-f(1)`. For N independent conditioned source draws the
KL bound is `N H^2/8`, and Pinsker gives joint TV at most
`min(1,sqrt(N) H/4)`. The pointwise log-likelihood difference is at most N H.
These are conservative, same-parameter model bounds. They do not certify that
the fitted parameters or a selected anomaly significance are unaffected. A
small per-source approximation must be assessed at the actual catalogue size.

## 5. Finite-bin boost response and its actual data qualification — derived

For an unresolved point-source population with integrated flux-density law
`S_nu proportional nu^(-alpha)`, Doppler factor
`D=1+beta.n+O(beta²)` gives `S'=D^(1+alpha)S` and the solid-angle factor D².
Let `g(S)=dN/(dOmega dS)` be positive differential counts and define
`N_b=integral_L^U g(S)dS`. If alpha is constant and selection is exactly this
flux bin, then

\[
 N'_b(D)=D^2\int_{L D^{-(1+\alpha)}}^{U D^{-(1+\alpha)}}g(S)dS,
 \qquad k_b=\left.\frac{d\log N'_b}{d\log D}\right|_1
 =2+(1+\alpha)\frac{L g(L)-U g(U)}{N_b}.
\]

For a joint distribution `g(S,alpha)`, integrate `(1+alpha)g(S,alpha)` at each
boundary instead. A hard upper boundary matters. For `g=K S^(-1-x)`,
`[L g(L)-U g(U)]/N_b=x`, so the familiar `k=2+x(1+alpha)` holds for every bin
of an exact power law. If the slope varies, an arbitrary fitted cumulative
threshold slope is not automatically the finite-bin response.

The inherited slope was `x=1.0431020647103473` over .020–.080 peak-proxy units,
with reported bootstrap SD .0028160522319821495. At the **assumed** alpha=.75,
this gives `k=3.825428613243108`, up to arithmetic rounding. This historical
measurement does not supply a full-population spectral response or certify
individual disjoint-bin coefficients. Using the rounded x=1.043 instead gives
3.82525, a harmless rounding distinction if labelled correctly.

For NVSS peak intensity, the point-source response requires an additional
morphology/beam argument. At an unresolved point-source image peak the numerical
Jy/beam value equals the source Jy flux in the usual beam normalization, but
extended sources do not follow that equality. Observed/deconvolved axes,
resolution flags and their noise/declination dependence must be interpreted
before defining an unresolved subset. A cut on fitted size also has a selection
response and can introduce spatial systematics. Do not label every small or
zero stored axis unresolved without verifying the catalogue's axis semantics.
The immediate count quotient remains legitimate as a peak-selected observable;
its conversion to beta is conditional on the chosen k_b and source law.

Generic selection-response functionals and simultaneous flux-bin boost fits are
already prior art: Takeuchi arXiv:2602.07389v2; Mittal & Lewis
arXiv:2605.27520; and Wagenveld et al. A&A697,A112 (2025), Eq.8, for shared
kinematic plus residual responses. The derivation here specifies the restricted
actual-data response, not a novelty claim about the generic formula.

## 6. Signed joint carrier, model comparisons and cross-bin dependence

Stack `X=(u_1x,u_1y,...,u_Bx,u_By)^T`, retaining signs, ordering and the
equatorial reference axis. Under the conditional independent-Poisson law,
disjoint bins have a product conditional likelihood and a block-diagonal model
information matrix. There is no identical-event shot-noise overlap. This fact
does **not** imply cosmological independence. For a Gaussian approximation
`X_hat~N(X,C)`, C must be the full adopted joint covariance.

The following fixed designs are distinct:

* Independent bin dipoles: `X=theta`, dimension 2B.
* Common transverse count dipole: `X=H a`, `H=1_B tensor I_2`, dimension two.
* Shared kinematic velocity with known responses: `X=K beta_perp`,
  `K=(k_1,...,k_B)^T tensor I_2`, dimension two when at least one k_b is nonzero.
* Shared velocity plus shared residual: `X=K beta_perp+H a`, dimension four
  only when the k_b are not all equal; otherwise the separation has rank two.

With `C=LL^T`, solve `min_theta ||L^-1(X_hat-D theta)||²` by QR/SVD. If D has
full column rank, `theta_hat=(D^T C^-1 D)^-1D^T C^-1 X_hat`, covariance
`(D^T C^-1 D)^-1`. The implementation should not explicitly invert C.
For fixed known C and a correct Gaussian model,

\[
 Q_D=(\widehat X-D\widehat\theta)^TC^{-1}
      (\widehat X-D\widehat\theta)\sim\chi^2_{2B-\operatorname{rank}D}.
\]

The fitted-mean Wald and Q_D are independent orthogonal Gaussian projections,
with dimensions rank(D) and `2B-rank(D)`. This statement requires fixed C;
estimated Poisson curvature or estimated extra dispersion gives an asymptotic
working approximation, not the exact law. Use supported quotient dimensions if
some bin information is rank-deficient.

For a common dipole, take any full-row-rank contrast matrix R of size
`2(B-1) by 2B` satisfying `R H=0`. Then

\[
 Q_H=(R\widehat X)^T(R C R^T)^{-1}(R\widehat X).
\]

This identity preserves cross-bin covariance; retaining only separate amplitude
errors does not. For shared beta choose a corresponding null-space basis of K.
The common-dipole and shared-beta models are nonnested when k varies: each may
be compared with the independent-bin model, but `Q_H-Q_K` is not a Wilks
chi-square statistic. A prescribed CMB beta vector is a fixed-mean model;
testing all 2B components against it uses dimension 2B, while a fitted common
beta model has only the residual dimension `2B-2`.

Exact conditional likelihood alternatives are available without Gaussian
compression: maximize `sum_b ell_b((D theta)_b)` for each design, retaining the
same ring totals and exposure. Likelihood-ratio laws are asymptotic under regular
interior fixed-rank conditions. Their degrees of freedom come from nested model
rank differences, not from names such as independent/common/kinematic.

### LSS and deterministic calibration

The inherited aggregate scalar C1 does not identify bin-specific redshift/bias
kernels, cross spectra or their masked response. In a full-sky pure-dipole
isotropic model, `Cov(d_ai,d_bj)=3 C1_ab delta_ij/(4pi)`, where

\[
 C_{1,ab}=\frac2\pi\int dk\,k^2P(k)K_a(k)K_b(k),\qquad
 K_a(k)=\int dz\,n_a(z)b_a(z)D(z)j_1(k\chi(z)).
\]

Actual masks and estimators transport these fields through their respective
responses; higher multipoles can leak into the estimated dipole. A single
aggregate C1 supplies none of the missing bin kernels or cross blocks.

One explicitly conditional sensitivity is a common field
`s~N(0,sigma_LSS² I_2)` with `sigma_LSS=.0021074779417` and
`C=C_P+sigma_LSS² H H^T`. It assumes the *same* transverse residual in all
bins. Then `R H=0` makes common-dipole contrasts exactly immune to this assumed
field, while the common-mode uncertainty grows. This cancellation is not true
for generic flux-dependent LSS. Reporting the sensitivity is useful; promoting
it to measured physical significance would require missing evidence.

For a deterministic omitted calibration mode g in the pixel log intensity, the
first-order local parameter bias is

\[
 \Delta u_b=J_b^{-1}\sum_rN_{br}
     \operatorname{Cov}_{q_{br}}(t,g),
\]

on the identified quotient. Ring-constant g cancels. A calibration dipole
`g=c.t` gives `Delta u=c` exactly to first order and is inseparable without an
external restriction. This is a concrete calibration vulnerability, not a claim
that nuisance projection removes all systematics. If a physically justified
bounded set `Delta X in B_cal` is supplied, use the confidence image
`E_X+B_cal` or optimize distances to that set; do not silently convert an
arbitrary budget into a Gaussian random covariance. A finite menu of cuts/models
is sensitivity evidence unless its common statistical construction is specified.

## 7. Conditional calibration and post-selection

For a fixed simple null `u_b=u_b0`, simulate independent multinomials in each
ring/bin with the observed `N_br` and probabilities `q_brp(u_b0)`. Refit exactly
the declared statistic, including failures, in every replicate. The Monte Carlo
test `p=(1+# {T_sim>=T_obs})/(M+1)` is valid by exchangeability, conservative with
ties when using >=; its finite resolution is `1/(M+1)`. Report M, the count and
binomial Monte Carlo uncertainty. This is conditional calibration under the
working count law, not a cosmological mock campaign.

For composite nulls with beta or a common dipole fitted from the same data, a
plug-in parametric bootstrap is generally approximate. It should refit nuisance
parameters in each replicate. Exact uniform coverage would require additional
conditioning or a valid supremum-over-nuisance construction. Wilks/Wald
approximations require positive identified information, a finite interior
estimate, fixed dimension and appropriate large-sample regularity. Do not claim
an exact chi-square law merely because the likelihood is concave.

Declination conditioning does not remove spatial clustering. Under a Cox process
or correlated source field the conditional ring count allocation is generally
not the independent multinomial law. Similarly, catalogue components can share
a parent object. Those are scientific-model failures, not optimizer errors.

If cuts, masks, binning or the reported statistic were chosen after seeing a
direction/amplitude, use the full prespecified joint object with simultaneous
coverage, simulate the entire selection procedure, or explicitly condition on
the selection event. For a fixed event A, the latter likelihood is

\[
 f_\theta(N\mid (N_{br}),A)
 =\frac{f_\theta(N\mid (N_{br}))\,1_A(N)}
 {\Pr_\theta(A\mid(N_{br}))}.
\]

The denominator cannot be dropped when it depends on theta. If a fixed-partition
selection is measurable entirely from conditioned totals, its effect disappears
upon conditioning; a data-dependent angular optimization generally is not of
this form. Nested flux thresholds share sources and cannot be multiplied as
independent likelihoods. Disjoint bins solve event overlap, not post-selection.

## 8. Concrete tensorized five-view construction

The canonical tuple is `(x,Q,Pi,F,G_F)`. These are pushforwards of one experiment,
not five primitive fitted parameters or independent likelihood factors. The
minimal output retains exact conditional sufficient statistics/normalizers,
the signed 2B-dimensional estimate, full covariance or likelihood, null basis,
bin labels/units, mask/exposure identity and the equatorial nuisance axis.

1. **x — signed functional bundle.** Retain X, predicted `D theta`, residuals,
   transverse dot products and contrasts, with all uncertainty transported from
   the same joint object. A scalar amplitude loses sign and direction. If a
   tensor summary is desired, form `M_bc=u_b u_c^T` or its symmetric/antisymmetric
   parts on the same draws/set; those are derived cross-bin tensor functionals,
   not independent data. The quadratic summaries do not generally determine the
   original vector (at minimum the global sign ambiguity remains).

2. **Q — matched reference body.** With an adopted positive-definite identified
   covariance C and rank nu, one statistical body is
   `A={x:x^T C^-1 x<=c_nu}`, where `c_nu=chi²_(nu,.95)` only under the stated
   Gaussian law. Its gauge is `Q(x)=sqrt(x^T C^-1 x/c_nu)`. The raw Mahalanobis
   radius is `r=sqrt(x^T C^-1 x)`. This is a coefficient-noise reference, not
   a physical MES ceiling or universal cosmological budget. A bootstrap region
   may replace the ellipsoid, with its own valid construction.

3. **Pi — named law and scalarization.** An example is the conditional null tail
   of the Wald/LR statistic for a stated mean/design. Another is a posterior
   exceedance under an explicitly supplied prior and posterior; it is a
   different question. The conditional Poisson significance cannot be relabelled
   a complete physical dipole-anomaly probability. Preserve numerical MC
   uncertainty and the response/LSS assumptions with each law.

4. **F — signed directional support.** For the same confidence ellipsoid
   `E={x:(x-X_hat)^T C^-1(x-X_hat)<=c_nu}`, the directional support is
   `h_E(a)=a^T X_hat+sqrt(c_nu a^T C a)` and the lower endpoint is
   `a^T X_hat-sqrt(c_nu a^T C a)`. Keep both antipodes. Divide by a named matching
   anchor support `h_A(a)>0` only when defined. If lifting to an unbounded
   three-dimensional physical set with free u_z, every functional with a z
   component has unbounded support; a finite 2D gauge does not bound 3D speed.
   Support utilization is not occupied volume or a probability.

5. **G_F — peak-flux levels and contrasts.** For B ordered bins use the invertible
   block map `T X=(u_1,u_2-u_1,...,u_B-u_1)` or adjacent contrasts with the first
   level retained. Transform `C_path=T C T^T` and `D_path=T D`. The same Gaussian
   quadratic is preserved; for the level-plus-difference map `|det T|=1` and
   the full Gaussian density agrees under change of variables. Discarding the
   first level loses the common mode. This is a **peak-flux path**, not a
   redshift/proper-time path, cosmological growth history, or a measured gradient
   of F. Signed zero crossings use differences, not unstable ratios.

RA-frame rotations act on every vector block and covariance consistently and
leave the registered scalar diagnostics invariant. A rotation of the physical
3D frame must also rotate the declination nuisance axis and exposure geometry;
rotating the vectors alone while holding the equatorial quotient plane fixed
does not represent the same model. An arbitrary Euclidean norm in whitened
coordinates is not a new physical tensor invariant: it is covariance-defined.

Five views can expose complementary behavior of an unchanged likelihood, for
example a large common mode with a small flux contrast, or strong apparent
amplitude with calibration-sensitive support. They cannot supply additional
independent evidence or recover a z component eliminated by the nuisance model.

## 9. Finite acceptance and publication boundary

The root's single verification pass can check: analytic score/Hessian against
finite differences; profile/conditional equality; the ring-shift invariance;
PSD/rank including one-pixel and two-pixel counterexamples; the linear-model
nonzero d_z derivative away from d_perp=0; exact normalizer/score sufficiency;
GLS/contrast equality with full off-diagonal C; path-transform likelihood equality;
and the shared-LSS contrast cancellation under its declared rank-two model.
The delivered `scripts/r65/verify_r65_algebra.py` (repository-root path) is a small exact symbolic oracle for some of
these identities, written but **NOT_EXECUTED in this lane**. It is not a catalogue
validation or an independent physical-response calibration.

Construction status: the exact log-linear quotient, rank characterization,
profile-information identity, physical-linear counterexample, finite-bin
response, GLS comparisons and five-view map are **derived**. Actual NVSS
identification ranks, estimates, likelihood gains, Monte Carlo tails, morphology
response, source-specific cross-bin LSS and selection robustness remain for the
parent's actual-data execution and stated limitations. No numerical PASS or
novelty-established claim is made here.

The defensible possible publication result is an actual-source measurement of
which transverse NVSS peak-selected count components survive arbitrary
declination-only nuisance, how disjoint-bin signed contrasts behave with their
real covariance, and how the conclusions change under explicitly bounded
calibration and response assumptions. Generic exponential-family conditioning,
GLS, score compression, multi-flux response fitting and five-view relabelling
are reused mathematics. A physical excess-speed claim additionally needs the
qualified spectral/morphology response and physical covariance. This bounded
construction does not establish a new strong no-go, a cosmological 3D velocity
measurement, or an independent CMB observer-boost likelihood.
