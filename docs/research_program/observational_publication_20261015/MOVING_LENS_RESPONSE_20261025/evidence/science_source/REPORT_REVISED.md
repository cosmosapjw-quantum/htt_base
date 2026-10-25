# R29 moving-lens source intake: revised response scope and estimator derivative

Revision 1, 2026-10-24. This separate author revision addresses F1/F2 in `/mnt/extdrive/workdir/htt_open_data/r29_moving_lens_source_independent_review/REVIEW.md` (review SHA256 `b3d771aadb12e9039396f0c97032239eb18a309ccc05e478d1945784eedd12e7`): nonlocal potential evolution for general spatial velocities, and data-dependent fitted weights. Original `REPORT.md` (SHA256 `52c4a64e6013ab9ed9ebec4b19787fd2d09322f49e980e0099f77882610f6126`) is retained unchanged as first-failure evidence. Source intake, raw sources and the K03 HOLD/no-new-numerical-packet decision are unchanged. The revised derivations await the existing independent reviewer's targeted closeout; author editing is not self-admission.

Date/access date: 2026-10-24. Owner: `htt`. Claim tier: C0; `CONDITIONAL`, non-claim-bearing source/theory intake. Transfer source: `empirical_proxy`; no native transfer. Requested runtime: `gpt-6-astra/xhigh`; observed model/effort: `UNKNOWN` / `NOT_INDEPENDENTLY_OBSERVED`. Consumer: root's decision whether an actual new K03 data-execution packet exists. This document changes no acceptance, DAG, claim registry, historical task, or publication state.

**Verdict: HOLD_SOURCE_SPECIFIC_PHYSICAL_RESPONSE. No new numerical moving-lens packet is justified by the sources obtained in this unit.** The ACT–DESI moving-lens route was already consumed on 2026-10-18. The present intake adds a bounded public-release check and an operator-specific identifiability analysis. It is not another independent observable node. Original K03 asks for nonradial physical observables and matching covariance for omega/A/beta, with independent source qualification and demonstrated nonradial response. That unchanged acceptance is not met by this intake. K04 also retains its separate H04 dependency.

Initial checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`, branch `research/htt-adaptive-methods-20261023`, HEAD `d93605e66adfececa89b90681124b232a5f90220`, origin `https://github.com/cosmosapjw-quantum/htt_base.git`. Existing tracked/untracked changes were present and untouched. All new files are under this external intake directory. No Git mutation, checkout copy, new worktree, child, numerical implementation, map calculation, old-campaign rerun, native solver or ODE occurred. Free space checked before retrieval: 2,460,801,204,224 bytes; later 2,460,800,659,456 bytes, well above the 2 GiB reserve. Only small selected source pages and source-code text were retained; no sky/catalogue archive was fetched.

## Prior evidence and primary-source result

Read the existing `OPEN_INPUTS_20261018/EXECUTION_20261018/MOVING_LENS_20261018/{REPORT.md,INDEPENDENT_REVIEW.md}`. Its conditional scalar-filter falsifier and error envelope remain the existing result; physical amplitude remains unbounded under its unbounded residual-error class. Its reviewed scope does not admit K03. Cached primary HTML/PDF were reused, not redownloaded or re-extracted into a new numeric result. Current byte checks match the recorded acquisition:

- `/mnt/extdrive/workdir/htt_open_data/moving_lens_20261018/2605.18938v1.html`: SHA256 `de9b8aabb3f7a4f8f57a37987710bb58712486c3ce23f4f5f498025855af0331`.
- Corresponding PDF: SHA256 `4e333fff8b7e2e25b0ebeb4aacf1dd5280026f774b2b2c61820da4cf4b4cf0da`.

The current [arXiv record](https://arxiv.org/abs/2605.18938) lists v1, submitted 18 May 2026. The [primary paper](https://arxiv.org/html/2605.18938v1) measures a template amplitude using ACT DR6 and DESI-LS DR9 LRGs. Relevant source locations are Eqs. 4, 17–25, 38–42 and Sections III.1, IV, V.3. The density reconstruction is potential-only. A weighted projected template is decomposed into angular gradient/curl, cross-correlated with temperature, and reduced to six bands and a fitted amplitude. Its normalization uses surrogate scalar-density fields; its galaxy–potential amplitude uses a halo model, with external lensing calibration deferred. The TC test is an ensemble-parity test. These are not released signed physical matter velocities or acceleration/vorticity estimates. No numerical measurement/covariance download link was found in this paper's links. Its quoted scalar detection is a source claim, not independently reproduced here.

## Bounded endpoint checks and exact retrieval gap

These endpoints exhaust the specific primary-paper/author/framework/official-product links followed in this unit. This is not a claim that every public server or unpublished author resource has been searched.

| Endpoint and observed identity | Observed material | Consequence for the consumer |
|---|---|---|
| [Author moving-lens page](https://selimhotinli.github.io/movinglenseffect/); corresponding page source commit `96777c7efc9fb2bdd7c2b77378193f4084dff1dc`, blob `f9cc8ee90727127723e7b6a147ca95dff21925cd` | Paper links, explanation, animation and result image; no numeric measurement bundle in Resources | Image is not a likelihood/covariance release; no digitization |
| [Author forecast repository](https://github.com/selimhotinli/moving_lens/tree/9e343c82930f0d8e4366507b5f1759f0559c8f09); README blob `e433b622c360d2e7d0d3db4b3c9a60a61a2732be`; releases API returned `[]` | Root contains only README; it postpones code/data availability until publication | Historical forecast repository, not evidence of an ACT-2026 release; no contact was made |
| [kszx](https://github.com/kmsmith137/kszx/tree/c64f3fda498b25cc978b2a67909f3c8f916578fd), full tree 99 entries, `truncated=false` | General source framework; `mlhack.py` blob `ed04d573d3e3168b6af03bc258c2dec79c6a7e34` provides scalar Fourier field to vector interpolation and spherical components | Genuine reusable ML helper, not a supplied ACT–DESI bandpower/covariance/calibration release; source was read, not executed |
| [kszx notebooks](https://github.com/kmsmith137/kszx_notebooks/tree/9dcce8cb4ce1f1e37074343444f0eae09d2bd046), full tree 17 entries, `truncated=false` | DESILS `pipeline_getsurrogates.ipynb`, blob `5edf87b897667509a7e33560dc47646522b89964`; no numerical moving-lens likelihood bundle in tree | A reconstruction/surrogate notebook does not establish the measurement's final configuration, weights, calibration or covariance |
| [ACT DR6.02](https://lambda.gsfc.nasa.gov/product/act/act_dr6.02/index.html), [NILC products](https://lambda.gsfc.nasa.gov/product/act/act_dr6.02/act_dr6.02_nilc_prod_table.html), [PSPIPE products](https://lambda.gsfc.nasa.gov/product/act/act_dr6.02/act_dr6.02_pspipe_prod_table.html) | Raw/component maps, beams/masks and ACT cosmology spectra/covariance/likelihood products are public | PSPIPE cosmology covariance is not covariance of the moving-lens TG/TC measurement; raw map availability alone does not close the response gap |
| [Zhou LRG v1 release](https://data.desi.lbl.gov/public/papers/c3/lrg_xcorr_2023/v1/), [catalogue listing](https://data.desi.lbl.gov/public/papers/c3/lrg_xcorr_2023/v1/catalogs/), [source paper Section 7](https://arxiv.org/html/2309.06443v2#S7) | Public main/extended catalogues, masks, imaging weights, photo-z information, clustering and redshift distributions. Listed FITS sizes: 545,264,640 and 1,484,357,760 bytes | These are real source inputs, not measured transverse-velocity products or the study's assigned true/observed-z randoms and surrogate realizations. No blind catalogue download |

GitHub exact-ID code search returned primary author/Quijote references and secondary mentions, not a linked numeric measurement bundle. General search also located two recent optical variants: [Wittman et al. 2609.38457v1](https://arxiv.org/html/2609.38457v1) analyzes actual Keck spectra but Section III.1 reports insufficient wavelength precision for the moving-lens effect; [Zhang et al. 2610.04865v1](https://arxiv.org/html/2610.04865v1) is a photon-noise forecast. Neither supplies the required cosmological transverse-field likelihood. They were checked to avoid treating a forecast as new measured data.

Small official HTML/README pages are preserved in `raw/`. Direct HTTP retrieval of those listed products succeeded with HTTP 200 after web-tool access errors on the DESI directory. A guessed obsolete ACT path and guessed GitHub `master` tree paths returned failures; corrected links/commit-qualified trees above succeeded. These failures are endpoint-resolution events, not scientific evidence of unavailable data. No authentication bypass was attempted.

## Restricted translated-lens response and a general-flow counterexample

The response below applies to a specified translated potential, or as a leading scale-separated approximation in which a long-wavelength bulk velocity is nearly constant across a short-wavelength potential. It is not a general physical law obtained by replacing that bulk velocity with an arbitrary spatial matter velocity. Assume scalar weak fields about flat FLRW, signature `(-,+,+,+)`, Born paths, nonrelativistic bulk motion and negligible intrinsic evolution during a lens crossing. Let comoving coordinates have length units, conformal time have time units, physical peculiar velocity be `v`, and `beta=v/c` refer to the CMB frame. Define dimensionless Weyl potential `phi=Phi_W/c^2`. These conventions and assumptions do not identify local peculiar motion with global matter tilt.

For a rigidly translated potential `phi(x,eta)=phi_0(x-X(eta))`, with `X'=v_bulk` constant across the lens, the chain rule gives `partial_eta phi=-v_bulk dot grad phi`. The transverse translation term in the linear ISW integral is therefore

\[
 \Theta_{\rm ML}(n)\equiv\Delta T/T_0
 =-2\int d\chi\,\beta_{{\rm bulk},\perp}^a\,
 \partial_{\perp a}\phi.
\]

For a thin lens define the unreduced deflection convention `alpha_a=2 integral dchi partial_a phi`. Then `Theta_ML=-alpha_a beta_bulk^a`. Alpha and beta are dimensionless; physical velocity is `c beta`. The translation term reverses under reversal of the bulk velocity at fixed potential and vanishes at zero bulk velocity or constant potential. Intrinsic ISW evolution is a separate term. This restricted natural-unit relation agrees with the source's moving-lens construction; it does not make its fitted `b_ML` equal to beta. The source's squeezed approximation, in particular Section III.1/Eq. 13, requires a long/short scale hierarchy. The domain is explicit in [Hotinli, Johnson and Meyers, 2006.03060v3, Section II](https://arxiv.org/html/2006.03060v3#S2), which takes velocity effectively constant over the halo integral. The review additionally identified [Wayland, Alonso and Coulton, 2609.04133v1, Section 2.1](https://arxiv.org/html/2609.04133v1#S2.SS1), inspected for this correction on 2026-10-24: their modeled moving-lens term uses coherent potential translation and excludes internal halo motion. This citation narrows the operator domain; it supplies no new measured physical field or covariance.

For a general spatial matter flow, a density-sourced gravitational potential evolves nonlocally. In the instantaneous Newtonian scalar subcase with negligible anisotropic stress, let `nabla^2 phi=kappa delta`, `kappa>0`, and use conformal-time continuity `delta'=-nabla dot[(1+delta)v]`. On a specified zero-mean periodic domain with the inverse Laplacian fixed, the velocity-dependent part is

\[
 \phi'_{v}=-\kappa\nabla^{-2}\nabla\!\cdot[(1+\delta)v].
\]

If the background coefficient evolves, the full derivative also includes `(kappa'/kappa) phi`; the comparison here holds kappa fixed at the snapshot or compares only the velocity-dependent contribution. This restriction is explicit and no periodic boundary condition is imported into the actual survey. The relevant inverse-Laplacian boundary/zero-mode prescription is part of a physical response contract.

The reviewer's analytic counterexample is decisive in this subcase. Take a periodic `(x,y)` domain, `k,q>0`,

\[
 \phi=\varepsilon\cos(kx),\quad
 \delta=-\frac{\varepsilon k^2}{\kappa}\cos(kx),\quad
 v=V\sin(qy)e_x,
\]

with `|epsilon| k^2/kappa<1` for positive matter density, `|epsilon|<<1` and `|V|/c<<1` for weak-field and slow-motion validity. The velocity is divergence-free and `curl v=-V q cos(qy) e_z`, while continuity and Poisson give

\[
 \delta'=-\frac{\varepsilon V k^3}{\kappa}\sin(kx)\sin(qy),\qquad
 \phi'_{v}=\frac{\varepsilon V k^3}{k^2+q^2}\sin(kx)\sin(qy).
\]

In contrast, local potential advection would give `-v dot grad phi=epsilon V k sin(kx) sin(qy)`. Their ratio is `k^2/(k^2+q^2)`, so at `q=k` the physical velocity-dependent derivative is one half of the local-advection expression. Both sides have units of inverse time. This is a symbolic snapshot counterexample, with no numerical run. It does not assert a global Bianchi solution. Its small `q/k` limit also shows why local advection can be a leading bulk/short-potential approximation while failing for arbitrary mode assignments.

## Full tangent carrier and the status of its response

For real orthonormal scalar harmonics, retain both tangent bases

\[
 Y^E_{\ell m,a}=\nabla_aY_{\ell m}/\sqrt{\ell(\ell+1)},\qquad
 Y^B_{\ell m,a}=\epsilon_a{}^b\nabla_bY_{\ell m}/\sqrt{\ell(\ell+1)}.
\]

With `N_r` declared radial basis functions `b_p(chi)`, `1<=ell<=L`, both `s=E,B` and all real signed `m` coordinates, the kinematic tangent carrier has dimension `2 N_r L(L+2)`. This dimension counts coordinates, not qualified physical degrees measured by the source. At fixed potential the expression

\[
 R^{\rm adv}_{\nu p\ell m s}=-2T_0 M_\nu B_\nu
 \left[\int d\chi\,b_p(\chi)\,\partial_{\perp a}\phi\,
 Y^s_{\ell m}{}^a\right]
\]

is a **formal advection Jacobian**. `B_nu` includes beam/filter/pixel operations and `M_nu` the mask. For arbitrary basis coefficients it is only the derivative of the stipulated local-advection model. It becomes a physical approximation only on a separately justified subspace of coherently translating or scale-separated bulk lenses, with its approximation remainder qualified. All signed E/B coordinates must remain visible when specifying which subspace, if any, is admissible; dropping unsupported coordinates is not evidence that they vanish.

Within that formal model, varying the potential adds `-2 T0 M B integral beta^a partial_a(delta phi) dchi`. A general physical response `R_phys` must instead be obtained from the source-compatible density/potential/velocity evolution, light-cone mapping, boundary prescription and any vector/tensor contributions required at the retained order. Source positions, selection and filtering may vary as well. The counterexample prevents using `R_adv` as an unrestricted replacement for `R_phys`.

No source-qualified map from common-congruence omega/A/beta fields to such a complete response was obtained. A single-epoch bulk velocity also does not independently supply four-acceleration. Without a dynamical/history closure, agreement of kinematic histories on the observed light cone need not fix their time derivatives; this is a missing-closure statement, not an assertion of freedom in every dynamical model.

## Three operators, compression and refitted weights

**Density reconstruction.** The source's `R_rho` maps scalar density into a longitudinal Fourier vector, so `k cross vhat=0` away from DC. Multiplication by galaxy density/weights and sky projection can nevertheless generate angular curl: `curl(rho vhat)=grad rho cross vhat` when `curl vhat=0`. Thus `X^C` may be nonzero. This algebra neither determines `R_phys` nor proves invisibility of all physical matter vorticity.

**Temperature response.** The restricted translated-lens response and the formal `R_adv` are distinguished above from the missing general `R_phys`. The presence of both E/B coordinate labels alone establishes no physical response rank. Conversely, neither potential-only reconstruction nor a TC parity test implies that genuine temperature data annihilate every physical solenoidal perturbation.

**Fixed bandpower operator.** With the observed template `X`, masks, beam/filter choices and bin weights fixed, TG/TC bands are a linear temperature map `d=L T`, so their tangent response is `delta d=L delta T`. If X or selection changes, add `(delta L)T`. For an actually specified fixed linear model `T=R u`, its deterministic bandpower kernel is `ker(LR)`. For a general nonlinear physical model, a derivative kernel is only a local first-order statement, not global indistinguishability. No evaluated actual-survey `R_phys` or physical null basis is supplied here.

**Fixed versus refitted amplitude.** Write `A=C^{-1}`, `h=t^T A t>0` and `w=A t/h`, on the domain where C is symmetric positive definite and t is nonzero. Then the fitted amplitude is `bhat=w^T d`. The expression `w^T L R` is its response only when **C and t are fixed**, as well as the bandpower operator. Fixed X alone is insufficient.

If C and/or t are recomputed, the full first differential is

\[
 d\hat b=w^T\,d\boldsymbol d+(d w)^T\boldsymbol d
 =\frac{t^T A\,d\boldsymbol d
 +(d t)^T A(\boldsymbol d-2\hat b t)
 -t^T A(d C)A(\boldsymbol d-\hat b t)}{h}.
\]

Here `d` preceding a quantity denotes its differential, whereas bold `d` is the bandpower vector. This uses `dA=-A(dC)A`. It includes template changes rather than treating the fiducial template normalization as constant by default. In the source's Eq. 23, C is an empirical function of unbinned `D_ell D_ell'`. With its multipole weights, support and cutoffs fixed,

\[
 dC_{bb'}=\frac{1}{W_bW_{b'}}\sum_{\substack{\ell\in b,\ell'\in b'\\|\ell-\ell'|\leq\Delta\ell}}
 w_\ell w_{\ell'}\left[(dD_\ell)D_{\ell'}+D_\ell(dD_{\ell'})\right].
\]

Changes to those weights/supports add their own terms. Holding the observed empirical covariance fixed is a possible conditional sensitivity question; recomputing the pipeline is a different one. These two procedures must not be conflated. A differentiable scalar output has a Jacobian of rank at most one at a point, but that fact is neither an observed physical rank nor a statement about the covariance information in the full data.

All signed modes, cross-frequency/cap/sample/depth covariance and the joint dependence of data, reconstructed X, template t, estimated C and physical calibration must accompany any eventual tensor inference. The covariance estimate and fitted weights are not independent observations. Scalar uncertainties or independent products cannot replace that joint structure.

A conditional ensemble example can be stated without the invalid general-advection substitution: **if** a particular fixed linear response H to a mean-zero random velocity perturbation w is independently justified, and w is independent of the scalar fields producing X, then `E_w[(Hw)X]=0`. This illustrates a blind direction of that specified cross-mean only. It does not assert that `H=R_adv` is physically valid for arbitrary w, or that the actual DESI velocity distribution obeys this independence. Temperature variance, cross-covariances and uncompressed maps can change. Parity cancellation likewise supplies no deterministic map null, full-likelihood blindness or physical vorticity bound.

## Concrete ambiguities that change the next action

1. **Normalization product ambiguity.** In the source's mean cross-spectrum, the physical velocity–template correlation and galaxy–potential calibration multiply. With either unconstrained, multiplying the former by positive `lambda` and the latter by `1/lambda` leaves every predicted bandpower unchanged. The surrogate/halo-model choices select a conditional normalization; they are not an observed joint calibration uncertainty for arbitrary new omega/A/beta models. This is an exact ambiguity of that observational parameterization, not a constructed pair of fully dynamical Bianchi solutions.

2. **Local lensing-gradient ambiguity.** For a thin-lens patch let `s_a` denote the effective nuisance coefficient of ordinary CMB-gradient lensing in the same unreduced-alpha convention. The shared dipolar part is `Theta_patch=alpha_a(s^a-beta^a)`. The simultaneous changes `beta -> beta+q`, `s -> s+q` leave every patch pixel unchanged. An independently measured large-scale CMB gradient and its covariance can constrain `s`; an unconstrained nuisance cannot. The [matched-filter paper](https://arxiv.org/html/2006.03060v3), Sections III, V and VI, explicitly discusses ordinary-lensing dipoles and halo-mass uncertainty. This conditional ambiguity does not deny that the source's scale separation can suppress contamination.

3. **A local internal-rotation/static-scalar-potential snapshot, with limited scope.** Use local physical radius `r`, spherical density/potential and `v=Omega cross r`, with Omega parallel to the patch line of sight. Here `div v=0` and `v dot grad delta=0`, so the continuity equation gives zero velocity-induced density derivative; the specified Poisson inverse gives zero velocity-induced scalar-potential derivative. Thus this snapshot's scalar ISW contribution from that rotation vanishes for either sign of Omega while `curl v=2 Omega`. This internal-motion example lies outside the coherent bulk-translation observable defined above. It uses continuity/Poisson, not an unrestricted advection identity, and cannot establish a rigid moving-halo no-go. It does not solve the full Euler/Einstein evolution or establish a global Bianchi or actual-DESI null. Intrinsic evolution and higher-order/vector-metric effects remain separate.

The first two ambiguities already block conversion of the released amplitude summaries to a qualified signed physical velocity field under an unspecified calibration/nuisance class. More processing of the old scalar summaries cannot remove them. An assumption setting the missing calibration or nuisance to its fiducial value would change the scientific question.

## Required payload, next transition, and claim audit

An execution that could change this source-specific decision needs an actual observed temperature/catalogue operator and its calibrated physical mapping. For consumption of the published measurement this means source-bound numerical TG/TC bands, exact template/window/mask/beam definitions, full channel/cap/sample covariance, realized velocity/potential normalization with uncertainty, and any calibration cross-covariance used in combination. For a new all-mode map analysis, it additionally means a declared common-frame physical response to the full signed E/B carrier, a justified evolution/boundary and scale-separation prescription, and a qualified lensing/foreground/selection nuisance class. Whether empirical covariance, template and selection are held fixed or refitted must be declared, with their derivatives and joint cross-dependence retained when they vary. The needed product is not the ACT cosmology PSPIPE covariance. The exact missing moving-lens release endpoint is **not supplied by the inspected primary links**; no URL is invented.

Root transition: reuse the completed 20261018 result and keep this route's original K03 contribution on HOLD; do not launch a new numerical unit merely because raw ACT/DESI inputs exist. Continue other independently ready source branches. Reopen this exact route when one of the inspected producer endpoints supplies the missing measurement/calibration product, or when the owner/controller defines a distinct fully qualified raw-map experiment. This source intake does not issue or consume a repair allocation and does not reset exhausted work.

Readback of published prose found **no moving-lens TC-to-vorticity overclaim** in the checked scope. `REPORT_20261024_REV1/sections/08_result_scope.tex:64` describes source-amplitude compression and explicitly rejects a transverse velocity interpretation; `figures/atlas.tex:492` retains the unbounded physical-amplitude limit. The existing 20261018 report likewise declines omega/A/beta conversion. No existing text correction or numeric recomputation is needed for these passages.

| Claim | Owner/status | Evidence and boundary |
|---|---|---|
| Existing route already analyzed | htt / observed source intake | Existing report/review and matching cached primary bytes; not new node completion |
| Translated-lens response; formal advection Jacobian | htt / DERIVED, CONDITIONAL | Rigid translation or qualified bulk/short-potential limit only; arbitrary E/B extension is formal. Poisson-continuity counterexample excludes a universal physical-advection law |
| Fitted-amplitude differential | htt / DERIVED, CONDITIONAL | Fixed C,t response separated from refitted C,t,X response; source Eq. 23 requires covariance derivative when recomputed; no physical rank measured |
| Missing physical calibration and cross-covariance | htt / source-intake HOLD | Inspected producer endpoints; bounded absence finding, not universal internet absence |
| TC parity null cannot be relabelled a full vorticity bound | htt / CONDITIONAL operator distinction | Weighted projection, true-temperature response and mean-compression statements kept separate |
| Full `(x,F,Pi,Q,G_F)` output from this intake | NOT_EVALUABLE | No qualified common-congruence tensor state, null/selection law or complete covariance; no scalars substituted for signed modes |

Skills applied: repository `htt-physics-math-audit`, `htt-claim-firewall`, `htt-claim-provenance-ledger`, and `htt-xqpi-fg-formalism` for carrier/law conventions. Skill guidance is a scope convention, not a mathematical oracle. No tests were rerun: there is no numerical-code change. The analytic counterexample, dimensions and full estimator differential were checked by hand; no numerical validation or CAS result is claimed. The existing reviewer's targeted closeout remains a separate decision from this author revision. No CAS certificate, native family identification, MIO posterior/truth claim, physical global-tilt measurement, or original-acceptance admission is made. Historical 17/42/alternate18, 48/R9 UNKNOWN and separately verified current counts remain untouched.
