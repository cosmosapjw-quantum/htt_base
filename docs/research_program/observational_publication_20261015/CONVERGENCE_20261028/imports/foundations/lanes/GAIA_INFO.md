# Gaia-INFO-01: which information must the carrier retain?

28 October 2026. Selected work: source reuse, constructive compression comparison and lightweight numerical discrimination (PhysMath 1.3, R2/R5/R7). This note is internal; no repository mutation, raw-catalogue replay, native solver or ODE evolution was performed.

## 1. The actual saved input

The experiment uses the exact saved `METHOD_EXECUTION_20261023/k03_depth_moments/RESULT.json` at active-branch commit `7f3f49a6b6d95b6ae0323d5bebd3afce0067b1a7`. Its Git blob is `e45d91abca9108e41136cea00ab1d641328e9537`; the runnable script checks that identity before computing. The source `compute.py` was also read at that commit to reconstruct the maps rather than guessing their meanings.

The source confirms 755,850 selected rows, a 102-column old nuisance design, six added slopes with $g(z)=z/(1+z)$, and the profiled information trace fraction

$$\frac{\operatorname{tr}F}{\operatorname{tr}A}=0.01584852677360534.$$

This is **1.5848527% in the declared parameter coordinates**, not information recovered by tensorization. Trace fractions change under a general rescaling of parameters. The saved generalized directional retentions are 0.01534238, 0.01541520, 0.01566121, 0.01572949, 0.01656432 and 0.01703457; generalized eigenvalues of the pair $(F,A)$ are invariant under invertible parameter reparameterization. Here the source's generalized spectrum is reused, whereas the trace fraction is directly checked from the saved $F$ and eigenvalues of $A$.

The 24-dimensional carrier has coordinates

$$y=(b_1,b_2,b_3,h),\qquad b_i,h\in\mathbb R^6,$$

where each six-vector contains **E1 polar Cartesian components followed by B1 axial Cartesian components**, in ICRS and microarcseconds per year. It is not an E2/STF shear carrier. The first 18 entries are the three old reported-redshift-bin intercepts; the last six are the new within-bin slopes. The full covariance is positive definite, with extreme eigenvalues 0.163201276 and 64.22579819 in squared microarcseconds/year.

At reported-redshift centres,

$$c=(1/4,7/12,26/33),\qquad Y_i=b_i+c_i h,$$

so $Y=Ty$ is 18-dimensional. Adjacent depth differences are $d=KY$, with blocks $(-I,I,0)$ and $(0,-I,I)$, giving a 12-dimensional carrier. The saved values and covariances of both maps are reproduced to floating-point precision. Their exact matrices are included in `GAIA_INFO.json`.

The retained Gaussian law is conditional on the original selected catalogue, stated nuisance model and independent-row working weights. The previous six-slope statistic 12.1402056890 and working-model tail 0.0589130888 are inherited unchanged. This work neither refits those rows nor interprets that tail as an empirical cosmological exclusion.

## 2. Two physical questions require different compressions

### 2.1 The original within-bin slope question

For the saved coefficient experiment, let

$$y\sim N(Jh+N\eta,C_{24}),\qquad
J=\begin{pmatrix}0_{18\times6}\\I_6\end{pmatrix},\quad
N=\begin{pmatrix}I_{18}\\0_{6\times18}\end{pmatrix}.$$

All bin intercepts remain arbitrary nuisance parameters. Profiling them gives the exact six-dimensional likelihood

$$-2\log L_p(h)= (y_h-h)^T C_{hh}^{-1}(y_h-h)+\text{constant},$$

where $y_h=y_{18:24}$ and $C_{hh}=C_{24}[18:24,18:24]$. The calculation reproduces the saved $F=C_{hh}^{-1}$. Thus a six-vector score or $y_h$ with its covariance retains the target's entire likelihood, not only its local Fisher matrix. Keeping all 24 coordinates is unnecessary once this target and nuisance model have been fixed.

However, reducing the carrier to bin-centre values $Y=Ty$ **before** fixing the question destroys this slope identification. Indeed, $TN=I_{18}$ and $TJ=\operatorname{stack}(c_iI_6)$ lies in its span. Every $h$ can be absorbed into the free bin means. The profiled information for $h$ in $Y$ is exactly zero. The code checks the column-span residual as zero. The twelve adjacent contrasts cannot repair this loss while the corresponding bin-mean differences remain arbitrary nuisance.

This is a concrete target-sensitive counterexample to treating the 24→18 map as universally harmless. It does not invalidate the 18-dimensional observable or its use for a different physical question.

A further useful equality holds: dropping covariance cross-blocks between the first three six-vectors and the last six **after this saved law is formed** does not change the above profiled slope likelihood, because only $C_{hh}$ remains. Correlations are not automatically important for every target. Their role must be derived from its response and nuisance projection.

### 2.2 A separate constrained cross-bin depth question

For a second experiment, stipulate the bin-mean family

$$Y_i=\alpha+c_i\vartheta+\epsilon_i,\qquad
\epsilon\sim N(0,C_Y),\quad C_Y=TC_{24}T^T.$$

Here the six-vector $\alpha$ is common across bins. This is a **different mean-family assumption** from arbitrary $b_i$ in the first experiment. It asks about the observable's coarse depth trend, not the original within-bin slope parameter. Its exact 18-dimensional GLS profile is equivalent to GLS on the 12 adjacent contrasts with $C_d=KC_YK^T$. A common spin/glide shift $N_{18}a$, $N_{18}=\operatorname{stack}(I_6,I_6,I_6)$, cancels under this profile; the numeric change in the inferred slope is below $10^{-10}$.

This matched experiment is where the independent-bin approximation is consequential. All methods see the **same** Gaussian draws from $C_Y$. Method B deliberately replaces it with its three diagonal 6×6 blocks. This is a diagnostic misspecified control, not the strongest published VSH estimator. C uses joint GLS; D uses the same carrier and law in transformed, normalized tensor coordinates.

## 3. What C versus D actually establishes

For any fixed invertible carrier transformation $x=By$, propagate every object:

$$J_x=BJ,\quad N_x=BN,\quad C_x=BCB^T.$$

The resulting profile likelihood, Fisher matrix and physical parameter confidence set equal those of the original GLS calculation. The test uses a nontrivial common spatial rotation and fixed positive E/B reference scales; the scales are declared microarcsecond/year references, not MES bounds. The maximum fitted-parameter difference is $2.42\times10^{-13}$ and the Fisher-matrix difference is $2.15\times10^{-16}$.

This tests **D's carrier/likelihood layer**. The additional $F,Q,\Pi,G_F$ interpretation must be defined as functions or images of this common inference object. They do not create extra likelihood factors. The result supports compatibility with optimal inference, not statistical superiority over correct joint GLS.

## 4. Scalar compression: genuine loss and genuine equality

Whiten the efficient six-slope carrier as $Z\sim N(\delta u,I_6)$ for a predeclared unit direction $u$. Its radial energy

$$R=\|Z\|^2\sim\chi'^2_6(\delta^2)$$

has the exact noncentral chi-square law. It was not approximated by a Gaussian likelihood on a norm.

At the null, every even compression $T(-Z)=T(Z)$ has zero score for the signed mean direction: its conditional score expectation vanishes by symmetry. Its local Fisher information in that signed parameter is zero. More generally, $T(Z)$ has identical distributions for $+\delta u$ and $-\delta u$; equal-prior sign classification therefore has best accuracy 1/2. The full signed likelihood has accuracy $\Phi(\delta)$, equal to **0.9937903 at $\delta=2.5$**. This global sign ambiguity persists even when local information about the positive amplitude grows away from zero.

The energy statistic's retained signed-amplitude Fisher fraction, integrated from its exact likelihood, is:

| $|\delta|$ | 0 | 0.5 | 1 | 2 | 2.5 | 3 | 4 | 5 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fraction | 0 | 0.07698 | 0.25154 | 0.58373 | 0.69196 | 0.76774 | 0.85834 | 0.90599 |

For a specified signed direction, the level-0.05 Neyman–Pearson test has exact power 0.80376494 at $\delta=2.5$. The scalar energy test has exact power 0.41933860. A 100,000-draw experiment gives 0.80370 (MCSE 0.00126) and 0.41871 (MCSE 0.00156), respectively.

The comparison must also retain its equality case: the correct six-parameter joint-GLS **omnibus** test has exactly the same energy statistic and power as this scalar test. If the desired question is only whether an unspecified six-vector is nonzero, this scalarization already gives the likelihood-ratio statistic. The power advantage above comes from preserving a specified physical direction, not from using six numbers as an end in itself.

## 5. Measured covariance effect in the declared cross-bin experiment

The following numbers use the actual saved covariance and 100,000 new Gaussian draws (seed 20261028), with a signal of Mahalanobis amplitude 2.5 along the declared least-informative direction. The source law, injection and target are identical across these rows.

| Method | Nominal covariance trace | Actual estimator covariance trace | 95% coverage | Power |
|:--|--:|--:|--:|--:|
| C joint GLS = D matched tensor coordinates | 24.83536 | 24.83536 | 0.94927 ± 0.00069 | 0.42130 ± 0.00156 |
| B diagonal bin blocks, nominal errors | 296.86857 | 25.96399 | 100000/100000 | 0/100000 |
| B point estimator, correct joint sandwich | 25.96399 | 25.96399 | 0.94976 ± 0.00069 | 0.40135 ± 0.00155 |

Errors shown are one Monte Carlo standard error. For the boundary counts, exact 95% binomial intervals are [0.9999631,1] for coverage and [0,0.00003689] for power. The nominal/actual error mismatch is not a new cosmological effect. Discarding the shared covariance destroys cancellation in a depth difference, producing an excessively broad confidence region. Correct sandwich errors repair coverage but leave a modest efficiency loss relative to joint GLS.

This result falsifies the idea that independent-bin treatment is harmless in this specific depth-mean family. It does not show that all separate VSH estimates are deficient: retaining their joint covariance makes them a valid route to C. The useful methodological result is the source-bound demonstration of where the covariance matters and the exact repair.

## 6. A minimum common carrier for more than one depth family

For the constrained bin experiment, compare response families $J_g=\operatorname{stack}(c_iI_6)$ and $J_{g^2}=\operatorname{stack}(c_i^2I_6)$ under the same $C_Y$ and common nuisance $N_{18}$. Whiten and project nuisance, then span both responses. The numerical rank of each is six and of their union is **twelve**.

Projecting onto an orthonormal basis of that union preserves the pairwise profiled likelihood ratio exactly. The source-data deviance difference is -67.77514657 in this working model, and its compressed versus full-profile difference is 0 to the recorded precision. This number is a calculation on the saved summary, not a validated preference for a physical cosmological history. The important result is the exact likelihood-ratio identity and rank audit.

Thus one six-vector score is enough after choosing one depth response. It is not automatically enough before comparing two response families. Their twelve-dimensional common carrier is the appropriate output of the response-family design, rather than either the original 24-vector or an early norm.

The code also tests the tempting alternative of using only the six-dimensional $g$-family score for both models. After that projection, both candidate response matrices have rank six and span the entire compressed space. Both families can therefore fit every compressed point exactly: their profiled deviance difference becomes zero, while the full/common-carrier difference is -67.77514657. Thus even a perfectly optimal score for one family's parameters can erase the information required to discriminate another family. This is a directly computed application of the common-carrier principle, with unrestricted linear amplitudes and the same fixed covariance in both models.

## 7. Common confidence events and robustness

In whitened six-dimensional coordinates, the common 95% ellipsoid covers in 0.95004 of the draws (MCSE 0.00069). Intersecting six separately reported marginal 95% intervals covers in only 0.73577 (MCSE 0.00139), matching $0.95^6=0.73509189$.

A common confidence set $\mathcal C$ can be pushed through any jointly defined vector of nonlinear physical functionals $\Phi$:

$$\theta\in\mathcal C\quad\Longrightarrow\quad\Phi(\theta)\in\Phi(\mathcal C).$$

For a Gaussian ellipsoid, the support of a linear functional $\ell^T\theta$ is $\ell^T\widehat\theta+\sqrt{q_{6,.95}\ell^TV\ell}$. This is a concrete place for directional $F$, a declared reference $Q$, probabilities under a separately stated law, and correlated depth images to operate. Correct joint GLS supports the same construction; the contribution must be the physical target and verified composition, not a claim to have invented simultaneous inference.

Fixed nuisance spin/glide shifts are removed exactly in the chosen cross-bin profile. An unmodelled bias outside that nuisance span raises false-positive rates: a one-Mahalanobis-unit bias gives exact probability 0.093559 rather than 0.05. Underestimating covariance likewise damages coverage; using the correct inflated covariance restores it. These are explicit sensitivity scenarios, not measured Gaia spatial covariance or measured selection bias. A tensor representation cannot repair a wrong data law.

## 8. Result and remaining empirical step

The original proposal is strengthened by a target-specific claim: preserve signed, jointly distributed carriers until response families and nuisance directions have been declared, then compress to their informative span. The saved Gaia example provides four actual outcomes: equality with correct GLS, exact sign-loss counterexamples, a numerically consequential cross-bin covariance error and repair, and a six-versus-twelve-dimensional common-carrier calculation.

The remaining physical step is the source-qualified mapping from these E1/B1 centroid coefficients to matter motion and its true-depth/reference-frame response. No STF shear, cosmic vorticity or MES radiation bound is inferred directly from this 24D carrier. That interface belongs to the physical foundation, while the present small experiment already validates its inference architecture under the saved law.

Reproduce with `OPENBLAS_NUM_THREADS=1 python code/gaia_info.py --draws 100000`. The script verifies its input blob, maps, covariance, exact GLS equivalences, sign symmetry, nuisance invariance and common-family likelihood ratio; results and Monte Carlo uncertainty are in `GAIA_INFO.json`. Figures are `figures/gaia_info_comparison.{png,pdf}` and `gaia_info_robustness.{png,pdf}`. The output includes fitted signed coordinates and covariances, rather than only scalar summaries.
