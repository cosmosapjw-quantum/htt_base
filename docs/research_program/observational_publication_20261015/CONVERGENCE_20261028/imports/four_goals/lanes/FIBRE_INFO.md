# FIBRE-INFO-01: detector-accessible internal drift and information preservation

28 October 2026. PhysMath 1.3 selected R2/R3/R5/R7/R9, with the scope and policies in `WORK_PACKET.md`. This lane derives and executes a finite positive two-state experiment. It uses the attached MF02 note, the previous target-qualified compression foundation and primary polarization/tomography literature. It does not fit an astronomical catalogue or evolve a Boltzmann hierarchy.

## 1. Source reuse and the actual normalization

The rendered MF02 PDF, p.17, §1.6.4, Eq.(1.6.8), already states the correct multiplicative expression

$$f(E,n)=f_0(E)[I+\varepsilon(n\cdot e)\sigma_3].$$

The pasted proposal drops the brackets and the factor multiplying the perturbation. This is a transcription difference, not a defect of the attachment. The additive expression with an energy-independent perturbation would need a separate positivity restriction: for example $f_0=0.1$ and $\varepsilon=0.2$ give an eigenvalue $-0.1$ in the most affected direction. That counterexample applies only to the literal pasted expression.

For a common finite-dimensional internal frame, extend the attachment's example to

$$f(E,n)=f_0(E)[I+(n\cdot e)\boldsymbol\theta\cdot\boldsymbol\sigma],
\qquad f_0\ge0,\quad \|\boldsymbol\theta\|\le1.$$

The eigenvalues are $f_0[1\pm |n\cdot e|\|\theta\|]$, so positivity is exact. Let

$$n_0=\int f_0(E)\frac{d^3p}{(2\pi\hbar)^3}$$

be the per-internal-channel number density. Isotropic angular integration gives

$$\mathsf n=n_0I,\qquad
\mathsf j^a=\frac{c n_0}{3}e^a\theta_i\sigma_i,
\qquad \mathsf v^a=\frac c3 e^a\theta_i\sigma_i.$$

The trace distribution, every total particle moment and the total stress tensor are independent of $\theta$. For the helicity case $\theta=(0,0,\varepsilon)$ and $R_\pm=(I\pm\sigma_3)/2$,

$$\frac{\operatorname{tr}(R_\pm\mathsf j^a)}{\operatorname{tr}(R_\pm\mathsf n)}
=\pm\frac{c\varepsilon}{3}e^a.$$

Thus the relative channel drift is physical in a specified measurement model even when it leaves the total stress unchanged. It is not an additional spacetime congruence or an Einstein-equation source independent of the traced matter stress. The causal matrix bound here is especially simple: $\sum_a\mathsf v^a\mathsf v_a=(c^2/9)\|\theta\|^2 I$.

The diagonal helicity example is globally meaningful as a scalar helicity-population contrast. The coherence extension in this experiment uses six discrete angular cells with specified fibre identifications and detector calibrations. It is not an assertion that a constant off-diagonal coefficient is a globally scalar field on the photon momentum sphere. MF02 §1.10 and Challinor's covariant polarization formalism distinguish the spin-weight-two Q/U field from helicity populations.

## 2. What is measured: positive effects, not matrix entries by declaration

For a detector axis $m_k$, the two effects are

$$R_{k,s}=\frac{I+s\,m_k\cdot\sigma}{2},\qquad s=\pm1.$$

Use the six angular directions $\pm\hat x,\pm\hat y,\pm\hat z$, each with weight $1/6$, and $e=\hat z$. This positive quadrature integrates the density, current and trace stress in the example exactly. Its joint photon law is

$$p(n,s\mid k)=\frac1{12}\{1+s(n\cdot e)[m_k\cdot\theta+\delta]\}.$$

Here $\delta$ is a specified common downstream signed-angular calibration offset in the count means. The domain requires $|m_k\cdot\theta+\delta|<1$. It is an observational nuisance, not a second matter drift. An identity-channel angular-selection term $\eta(n\cdot e)$ can be added inside the braces when all probabilities remain nonnegative. It cancels from the marginal of $r=s(n\cdot e)$ conditional on $|n\cdot e|=1$. The fitted experiment uses this marginal.

For $N_k$ photons in setting $k$, the number $n_k$ in the informative two angular cells is Binomial$(N_k,1/3)$, independently of the parameters. Conditional on $n_k$, the number $K_k$ with $r=+1$ is

$$K_k\mid n_k\sim\operatorname{Binomial}\!\left(n_k,\frac{1+t_k}{2}\right),
\qquad t_k=m_k\cdot\theta+\delta.$$

This is the sampling law used below. Storing a Hermitian matrix in software does not provide these counts. The x/y/z settings require distinct analyzer actions on separately assigned photons; simultaneous incompatible outcomes are not assumed.

At $\theta=\delta=0$, each informative photon contributes $m_km_k^T$ to the physical information. For equal exposures, let $M$ have rows $m_k^T$. An unknown common calibration offset gives

$$I_{\theta\mid\delta}\ \propto\ M^T\left(I-\frac{11^T}{K}\right)M.$$

The general nuisance-quotient condition is the one in the user's proposal: no nonzero physical direction may have the same measurement image as an allowed nuisance direction. This is standard local identifiability; its application below tells which physical information the chosen detector actually supplies.

| Measurement design | Rank with calibrated offset | Rank after unknown common offset |
|:--|--:|--:|
| Trace only | 0 | 0 |
| One helicity analyzer | 1 | 0 |
| x/y/z analyzers | 3 | 2 |
| Two calibrated converting paths, effective z and x effects | 2 | 1 |
| Six physically balanced effects, ±x/±y/±z | 3 | 3 |

The balanced design has $M^T1=0$, so the common offset is orthogonal to all three physical directions at the unpolarized reference. The opposite settings must be physically realized analyzer/converter settings with the stipulated downstream nuisance behavior. Merely renaming the two outcomes also changes the nuisance sign and does not implement this calibration design.

## 3. A sharp transport qualification: geometric helicity phases are not arbitrary SU(2) conversion

With a calibrated transfer $U_\gamma$, the relevant source effect is

$$R^{\rm eff}_\gamma=U_\gamma^\dagger R_oU_\gamma.$$

The span of these effective effects determines accessibility. Two generic calibrated conversion paths can expose two independent components, but they cannot identify all three components of an unrestricted qubit Bloch vector.

For the purely geometric photon helicity connection, in a helicity frame,

$$U_\gamma=\operatorname{diag}(e^{i\psi_\gamma},e^{-i\psi_\gamma}).$$

It commutes with $\sigma_3$. Consequently any number of such paths followed by a helicity detector retains rank one. A linear analyzer is rotated within the $\sigma_1,\sigma_2$ plane; distinct phases can supply rank two, but no helicity component. A specified mixing interaction or a helicity-sensitive analyzer is needed for the remaining direction. The numerical checks return ranks 1 and 2, respectively.

This is the appropriate role for $G_F$: keep the calibrated comparison map and its attainable effect span. A change of fibre coordinates does not add photons or information. Indeed, under endpoint changes $G_s,G_o$,

$$f_s'=G_sf_sG_s^\dagger,\quad
U'=G_oUG_s^\dagger,\quad R_o'=G_oR_oG_o^\dagger,$$

all pairings $\operatorname{tr}(R_oUf_sU^\dagger)$ are unchanged. The executed residual is $1.11\times10^{-16}$.

## 4. Exact sufficient counts depend on the nuisance family

This finite experiment strengthens the previous Gaussian lesson without presuming a Gaussian law. With known $\delta=0$, opposite-axis observations can be pooled. For component $i$,

$$S_i=K_{+i}+(n_{-i}-K_{-i})
\sim\operatorname{Binomial}\!\left(n_{+i}+n_{-i},\frac{1+\theta_i}{2}\right).$$

The three $S_i$, conditional on the known exposures, are sufficient for all three components. If only the helicity drift is the target, the corresponding one-dimensional count is sufficient under its stated nuisance model. Full matrix storage is unnecessary after that question is fixed.

If the common offset is unknown, the two probabilities instead depend on $\delta+\theta_i$ and $\delta-\theta_i$. Pooling the opposite outcomes is no longer likelihood preserving. On an open four-parameter family, the six natural parameters

$$h(\delta+\theta_i),\ h(\delta-\theta_i),\qquad
h(t)=\log\frac{1+t}{1-t},$$

span six dimensions. To see this, evaluate derivatives at $\theta=0$ and a nonzero admissible $\delta$. The first derivatives in each $\theta_i$ give the three antisymmetric pair directions. Since $h''(\delta)\ne0$, the second derivatives give the three symmetric pair directions. These six directions are independent. Therefore a fixed **linear compression of the six count statistics** preserving the whole declared likelihood needs rank six; a local four-component score need not preserve its finite likelihood ratios. The known-zero-offset family instead spans rank three. Numerical SVD reproduces ranks 6 and 3.

This is an application of curved exponential-family sufficiency, not a proposed new general theorem. It makes the physical lesson explicit: calibrating the downstream nuisance can reduce the required retained carrier, while pretending it is calibrated can erase finite-likelihood information.

## 5. Common-event physical confidence images

Construct simultaneous two-sided Clopper–Pearson intervals $[l_k,u_k]$ for all six $t_k$, each at error probability $\alpha/6$. Conditional on the ancillary $n_k$, their common event has coverage at least $1-\alpha$. Define

$$\mathcal C_\alpha=
\{\theta:\|\theta\|\le1,\ \exists\delta,\quad
l_k\le m_k\cdot\theta+\delta\le u_k\ \forall k\}.$$

This is a direct physical confidence image. The actual drift tensor belongs to $(c/3)e^a\mathcal C_\alpha\cdot\sigma$ on the same event. For a candidate $\theta$, existence of a common offset is checked by the scalar inequality

$$\max_k(l_k-m_k\cdot\theta)\le
\min_k(u_k-m_k\cdot\theta).$$

At $\theta=0$, this reduces to whether all six intervals intersect. Excluding zero means no common instrumental offset can explain the observed signed channel contrasts within that confidence event. It does not, by itself, identify geometric shear or vorticity.

The exact construction is intentionally compared with the simpler three-component Wald ellipsoid, rather than assuming that positivity and a representation guarantee statistical coverage.

## 6. Executed comparisons

The reproducible script uses 6,000 photons per realization, 1,000 for each balanced analyzer setting, and 100,000 realizations per case. The common calibration offset is 0.025. All analysis views are reductions of the same acquired count law. The rank table above compares possible hardware/effect designs separately; different designs are not labelled the same experiment.

| Input theta | Joint Wald 95% coverage | Exact six-channel event coverage | Projected physical-image coverage | Joint Wald rejection | Helicity-z rejection | Exact image excludes zero |
|:--|--:|--:|--:|--:|--:|--:|
| (0,0,0) | 94.823% | 95.897% | 99.797% | 5.177% | 5.064% | 0.203% |
| (0.1,0,0) | 94.877% | 95.869% | 99.824% | 57.437% | 5.076% | 13.004% |
| (0,0,0.1) | 94.829% | 95.794% | 99.806% | 57.166% | 73.586% | 13.093% |
| (0.12,0.08,0.06) | 94.815% | 95.817% | 99.823% | 93.976% | 34.587% | 39.990% |

Monte Carlo standard errors and exact binomial intervals for all these rates are in `FIBRE_INFO.json`. The nominal Wald image slightly undercovers. The finite common-event construction has a guarantee, but its Bonferroni and nuisance projection are substantially conservative. This efficiency cost is an observed result, not hidden by calling the region “95%”. A calibrated joint count-likelihood region is the specific next statistical refinement.

At equal prior odds for $\theta=(0,0,+0.08)$ versus $(0,0,-0.08)$ and zero calibration offset, exact count-likelihood classification is **98.086%** correct, Monte Carlo SE 0.0433 percentage points, with a fair randomized decision at the 155 exact likelihood-ratio ties. The corresponding expected success with half credit for ties is 98.0895%. A dedicated sign-only rerun records this review correction; all other Monte Carlo results remain unchanged. Trace counts have identical laws and yield chance accuracy 50%. Sorted eigenvalues of the ideal state also agree between the two signs, while the calibrated helicity labels distinguish them. This is a loss of the specified channel orientation, not a universal inferiority of scalar sufficient statistics.

The pure helicity test has higher power than the three-component omnibus test for a helicity-only signal, while it is blind to the injected x coherence. The target determines which retained directions and which test are useful.

![Finite detector ranks, same-count rejection probabilities and a specified CP dephasing loss. The middle panel is the Wald comparison and has the small coverage shortfall reported in the table. Generic converting paths in the left panel are distinct from the restricted geometric helicity connection.](../figures/fibre_info_comparison.png)

## 7. A specified CP loss and a finite likelihood-error certificate

As a finite channel control, take

$$\mathcal E_\lambda[\rho]
=\frac{1+\lambda}{2}\rho+
\frac{1-\lambda}{2}\sigma_3\rho\sigma_3,
\qquad 0\le\lambda\le1.$$

This completely positive trace-preserving dephasing channel maps $(\theta_1,\theta_2,\theta_3)$ to $(\lambda\theta_1,\lambda\theta_2,\theta_3)$. With the fixed balanced measurement at the unpolarized reference, retained Fisher fractions are exactly $(\lambda^2,\lambda^2,1)$. At complete dephasing, only the helicity direction remains. This is a specified channel control; the Thomson kernel is a different physical channel addressed by the radiation lane.

The count experiment also admits a simple finite compression/response certificate. If exact and approximate contrasts obey $|t_k|,|\widetilde t_k|\le1-\gamma$ and $|t_k-\widetilde t_k|\le e_k$, then differentiation of the binomial log likelihood gives

$$|\ell(t)-\ell(\widetilde t)|\le
\sum_k\frac{n_ke_k}{\gamma}.$$

For a two-candidate likelihood ratio, add the two respective bounds. A trace-zero state error at a normalized binary effect gives $|\Delta t_k|\le\|\Delta\rho\|_1$. A calibrated unitary error $\|U-\widetilde U\|_{\rm op}\le\xi$ gives $\|U\rho U^\dagger-\widetilde U\rho\widetilde U^\dagger\|_1\le2\xi$. Thus source, truncated internal moment and calibrated transport allowances can be propagated into a finite observational likelihood budget before compression. The bound is conservative near low-probability outcomes; its probability margin is explicit.

## 8. Interpretation within the existing five coordinates

- $x$: the sufficient count carrier after the physical target and nuisance family are fixed; six channels are retained when the common offset is unknown.
- $F$: support of the common physical image in detector-relevant Hermitian directions. It retains channel sign and orientation, with nonconvex physical images retained separately if present.
- $Q$: a declared gauge, for example the unit-ball normalization of $\theta$, equivalent here to $3\|e_a\mathsf v^a\|_{\rm op}/c$ along its specified spatial axis. Physical admissibility and statistical uncertainty keep distinct provenance.
- $\Pi$: the probability of a named event under the common count law or a separately specified posterior. The single-photon Born probabilities generate the count law; they are not another independent likelihood factor.
- $G_F$: calibrated fibre comparison/conversion maps, selection and cross-window probability law; the effective-effect span states what their comparison can reveal.

The immediate physical contribution is a detector-level account of internal drift which is absent from the total stress, together with a finite inference and compression contract. Connecting it to FLRW departure requires a named radiation/matter forward response. In particular, a nonzero helicity drift does not alone establish nonzero geometric vorticity or anisotropic expansion.

## 9. Evidence, literature and smallest next unit

Source locations: MF02 p.17 §1.6.4 for the trace-hidden current; pp.28ff §1.10 for Stokes/spin weights; §1.16 for photon screen transport. The current experiment reuses the prior HTT common-confidence-image and target-qualified-compression framework, while replacing its Gaussian law by explicit photon counts.

Primary comparison: James, Kwiat, Munro and White, *On the Measurement of Qubits*, Phys. Rev. A 64, 052312 (2001), https://arxiv.org/abs/quant-ph/0103121, develops polarization tomography, positivity and error propagation. Challinor, *Microwave background polarization in cosmological models*, Phys. Rev. D 62, 043004 (2000), https://arxiv.org/abs/astro-ph/9911481, supplies the covariant polarization/PSTF setting; its source uses (+---) and c=1, so those conventions are not copied into the present (-+++) dimensional interpretation. Zhuravlev and Filippov, https://arxiv.org/abs/2004.00966, examines informational completion by measurement dynamics; its repeated-instrument scenario is a comparator, not the same physical protocol as the calibrated paths here. These precedents rule out novelty claims for density-matrix tomography or generic information recovery by additional measurements. The concrete contribution candidate is the cosmological response/nuisance/transport application with an explicit physical target and finite error contract.

`code/fibre_info.py` reproduces the counts, covariance tests, exact-event image, natural-parameter span and plot. The current/stress quadrature residuals are $2.78\times10^{-17}$ and zero; the gauge pairing residual is $1.11\times10^{-16}$; the CP-channel residual is $1.52\times10^{-16}$. Wolfram independently returned the exact density/current matrices and determinant $1-\varepsilon^2\cos^2\vartheta$. Its initial context call failed at the tool layer; the subsequent evaluator result is preserved separately. A NumPy empty-design rank edge case was repaired by assigning its mathematical rank zero; the execution receipt records it. The raw initial run log retains the former strict-sign success metric; `fibre_info_SIGN_REPAIR.json` supplies the corrected equal-prior classification result with explicit tie handling.

The smallest next experiment is to substitute an actual calibrated polarimetric response for the ideal Pauli settings, compute the nuisance-quotient effect span, and construct a joint count-likelihood confidence image with better efficiency than the current Bonferroni outer image. The operator should come with its allowed helicity/coherence transformations; a generic SU(2) converter must not be inferred from a photon screen connection. No new hierarchy solver is required for this unit.
