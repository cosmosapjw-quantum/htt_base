# R29 moving-lens source intake: existing route, unresolved physical response

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

## Weak-field physical response and full tangent dimensions

The following is this intake's derivation under explicit assumptions, not a fit or an admitted cosmological transfer. Assume scalar weak fields about flat FLRW, signature `(-,+,+,+)`, Born light paths, slow nonrelativistic lens translation, and negligible intrinsic potential evolution during a lens crossing. Let comoving spatial coordinates have length units, conformal time have time units, physical peculiar velocity be `v`, and `beta=v/c` be defined in the CMB frame. Define dimensionless Weyl potential `phi=Phi_W/c^2`; spatial gradients are comoving. Local boost, halo peculiar motion and global matter tilt remain separate quantities.

Advection gives `partial_eta phi = -v^a partial_a phi`. Substitution in the linear ISW integral gives the translation contribution

\[
 \Theta_{\rm ML}(n)\equiv\Delta T/T_0
 =-2\int d\chi\,\beta_\perp^a(\chi,n)\,\partial_{\perp a}\phi(\chi,n).
\]

For a thin lens whose bulk transverse velocity is constant across the potential, define the unreduced deflection convention `alpha_a=2 integral dchi partial_a phi`. Then `Theta_ML=-alpha_a beta^a`. Alpha and beta are dimensionless; physical velocity is `c beta`. The signal reverses under beta reversal at fixed potential and vanishes for zero velocity or constant potential. The natural-unit form agrees with the source's response. It does not make the source's fitted `b_ML` equal to beta.

For real orthonormal scalar harmonics, use both tangent bases

\[
Y^E_{\ell m,a}=\nabla_aY_{\ell m}/\sqrt{\ell(\ell+1)},\quad
Y^B_{\ell m,a}=\epsilon_a{}^b\nabla_bY_{\ell m}/\sqrt{\ell(\ell+1)}.
\]

With `N_r` declared radial basis functions `b_p(chi)` and `1<=ell<=L`, retain all signed real coefficients `u^s_{p ell m}`, both `s=E,B` and all `m`. The tangent dimension is `2 N_r L(L+2)`. Conditional on a fixed calibrated potential, the temperature response column before compression is

\[
 R_{\nu p\ell m s}=-2T_0\,M_\nu B_\nu
 \left[\int d\chi\,b_p(\chi)\,\partial_{\perp a}\phi\,
 Y^s_{\ell m}{}^a\right],
\]

where `B_nu` includes the released beam/filter/pixel operator and `M_nu` the actual survey mask. For arbitrary finite coefficients this is a map-valued response, not one radial or scalar score. If potential/calibration changes, the additional first variation is `-2 T0 M B integral beta^a partial_a(delta phi) dchi`; source positions, selection and filtering also have response terms. Those terms cannot be silently set to zero.

The final physical parameter response would require a source-qualified Jacobian from the chosen common-congruence omega/A/beta fields to these velocity and potential changes. None was obtained. In particular a single-epoch velocity response is not an independent four-acceleration response. Without a specified dynamical/history closure, histories agreeing on the sampled light cone can have different time derivatives. This is a kinematic missing-response statement, not a claim that all dynamical models have this freedom.

## Three different operators and their different null statements

**Density reconstruction.** The source's `R_rho` maps a scalar density into a longitudinal Fourier vector. Its `k cross vhat=0` follows algebraically away from DC. It has no freely selectable 3D solenoidal input. However multiplying by galaxy density/weights and projecting onto the sky can produce angular curl: `curl(rho vhat)=grad rho cross vhat` even when `curl vhat=0`. Nonzero `X^C` is therefore possible. Neither fact proves that true matter vorticity is invisible to temperature.

**True temperature response.** `R` above contains both tangent E and B velocity perturbations. There is no general identity annihilating all B modes. A genuine temperature map could respond to a true solenoidal velocity, subject to potential, frame, survey and nuisance qualifications.

**Source compression.** At fixed observed template `X`, each retained TG/TC bandpower is a linear functional of temperature, hence has response `L R`; its fitted scalar has response `w^T L R`. For one scalar the linear rank is at most one. All channels/samples require their shared covariance; their number alone does not give independent physical directions. For any specified finite compression, its exact unresolved directions are `ker(L R)` after any justified nuisance quotient. The source supplies no evaluated all-mode `L R`, so no numerical rank/null basis for the actual survey is asserted here.

A conditional **ensemble** example illustrates the curl limitation: add a mean-zero solenoidal velocity field `w` statistically independent of all density/potential fields used to construct `X`. At fixed scalar fields, `E_w[T_ML(w) X]=0`, because temperature is linear in `w`. Its TG and TC mean cross-correlations are unchanged, despite nonzero vorticity realizations. Variance and uncompressed temperature can change. Thus this is a null sector of the modeled cross-mean under declared independence, not a deterministic map null, not a universal statistical null and not a physical vorticity upper bound. Parity cancellation alone has the same limited scope.

## Concrete ambiguities that change the next action

1. **Normalization product ambiguity.** In the source's mean cross-spectrum, the physical velocity–template correlation and galaxy–potential calibration multiply. With either unconstrained, multiplying the former by positive `lambda` and the latter by `1/lambda` leaves every predicted bandpower unchanged. The surrogate/halo-model choices select a conditional normalization; they are not an observed joint calibration uncertainty for arbitrary new omega/A/beta models. This is an exact ambiguity of that observational parameterization, not a constructed pair of fully dynamical Bianchi solutions.

2. **Local lensing-gradient ambiguity.** For a thin-lens patch let `s_a` denote the effective nuisance coefficient of ordinary CMB-gradient lensing in the same unreduced-alpha convention. The shared dipolar part is `Theta_patch=alpha_a(s^a-beta^a)`. The simultaneous changes `beta -> beta+q`, `s -> s+q` leave every patch pixel unchanged. An independently measured large-scale CMB gradient and its covariance can constrain `s`; an unconstrained nuisance cannot. The [matched-filter paper](https://arxiv.org/html/2006.03060v3), Sections III, V and VI, explicitly discusses ordinary-lensing dipoles and halo-mass uncertainty. This conditional ambiguity does not deny that the source's scale separation can suppress contamination.

3. **A local exact rotation example, with limited scope.** Use local physical radius `r`, a stationary spherical Newtonian potential, and rotation `v=Omega cross r` with Omega parallel to the patch line of sight. Then v is transverse and `v_perp dot grad_perp Phi_W=0` pointwise whereas `curl v=2 Omega`. The translation-order moving-lens temperature is zero for either sign of Omega. This demonstrates why a generic local matter-curl interpretation needs a matter-to-potential closure. It is not a claim about all large-scale rotational modes, a global FLRW/Bianchi solution, or the specific DESI likelihood. Higher-order/vector-metric effects lie outside the assumed scalar response.

The first two ambiguities already block conversion of the released amplitude summaries to a qualified signed physical velocity field under an unspecified calibration/nuisance class. More processing of the old scalar summaries cannot remove them. An assumption setting the missing calibration or nuisance to its fiducial value would change the scientific question.

## Required payload, next transition, and claim audit

An execution that could change this source-specific decision needs an actual observed temperature/catalogue operator and its calibrated physical mapping. For consumption of the published measurement this means source-bound numerical TG/TC bands, exact template/window/mask/beam definitions, full channel/cap/sample covariance, realized velocity/potential normalization with uncertainty, and any calibration cross-covariance used in combination. For a new all-mode map analysis, it additionally means a declared common-frame all-E/B response and qualified lensing/foreground/selection nuisance class. The needed product is not the ACT cosmology PSPIPE covariance. The exact missing moving-lens release endpoint is **not supplied by the inspected primary links**; no URL is invented.

Root transition: reuse the completed 20261018 result and keep this route's original K03 contribution on HOLD; do not launch a new numerical unit merely because raw ACT/DESI inputs exist. Continue other independently ready source branches. Reopen this exact route when one of the inspected producer endpoints supplies the missing measurement/calibration product, or when the owner/controller defines a distinct fully qualified raw-map experiment. This source intake does not issue or consume a repair allocation and does not reset exhausted work.

Readback of published prose found **no moving-lens TC-to-vorticity overclaim** in the checked scope. `REPORT_20261024_REV1/sections/08_result_scope.tex:64` describes source-amplitude compression and explicitly rejects a transverse velocity interpretation; `figures/atlas.tex:492` retains the unbounded physical-amplitude limit. The existing 20261018 report likewise declines omega/A/beta conversion. No existing text correction or numeric recomputation is needed for these passages.

| Claim | Owner/status | Evidence and boundary |
|---|---|---|
| Existing route already analyzed | htt / observed source intake | Existing report/review and matching cached primary bytes; not new node completion |
| Weak-field tangent response above | htt / DERIVED, CONDITIONAL | Explicit scalar/Born/advection assumptions; no numerical or independent scientific validation claimed |
| Missing physical calibration and cross-covariance | htt / source-intake HOLD | Inspected producer endpoints; bounded absence finding, not universal internet absence |
| TC parity null cannot be relabelled a full vorticity bound | htt / CONDITIONAL operator distinction | Weighted projection, true-temperature response and mean-compression statements kept separate |
| Full `(x,F,Pi,Q,G_F)` output from this intake | NOT_EVALUABLE | No qualified common-congruence tensor state, null/selection law or complete covariance; no scalars substituted for signed modes |

Skills applied: repository `htt-physics-math-audit`, `htt-claim-firewall`, `htt-claim-provenance-ledger`. No tests were rerun: there is no numerical-code change. Dimensional, sign and zero-response limits are shown above; a subsequent independent theory decision is distinct from this author's intake. No CAS certificate, native family identification, MIO posterior/truth claim, physical global-tilt measurement, or original-acceptance admission is made. Historical 17/42/alternate18, 48/R9 UNKNOWN and separately verified current counts remain untouched.
