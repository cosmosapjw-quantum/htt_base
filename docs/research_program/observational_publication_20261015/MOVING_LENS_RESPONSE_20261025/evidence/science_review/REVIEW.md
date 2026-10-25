# R29 moving-lens independent source/theory review

Date: 2026-10-24. Reviewer: /root/r29_moving_lens_source_independent_review. Requested runtime: gpt-6-astra/xhigh. Observed model/effort: UNKNOWN / NOT_INDEPENDENTLY_OBSERVED. This is an independent read-only source/theory review; the reviewer did not author the intake.

Reviewed candidate: /mnt/extdrive/workdir/htt_open_data/r29_nonradial_moving_lens_intake/REPORT.md
SHA256: 52c4a64e6013ab9ed9ebec4b19787fd2d09322f49e980e0099f77882610f6126

**Decision: HOLD_TEXT_REPAIR_REQUIRED for the candidate's physical-operator description. SCOPED_PASS for retaining the source-specific scientific HOLD and declining a new numerical packet.** Two bounded corrections are required below. Neither requires a numerical run or changes the original K03 acceptance.

## Findings and targeted acceptance wording

### F1 — P2: the advection Jacobian is not a general matter-velocity response

Location: candidate lines 37–43, 55–71; consequently the interpretation at line 83.

The thin translated-potential expression is sound with the stated alpha convention. However, “arbitrary finite coefficients” and the “True temperature response” label extend it beyond rigid or slowly varying bulk translation. A spatially varying matter velocity does not generally advect its gravitational potential pointwise: Poisson inversion does not commute with multiplication by a spatially varying velocity.

The limitation is explicit in primary literature. [Hotinli, Johnson and Meyers, arXiv:2006.03060v3, Section II after Eq. 4](https://arxiv.org/html/2006.03060v3#S2) assumes a velocity effectively constant across the halo integral. [Hotinli et al., arXiv:1812.03167v1, Estimator](https://arxiv.org/html/1812.03167v1#S2) reconstructs large angular velocity scales using much smaller-scale density/temperature structure. A focused source search additionally found [Wayland, Alonso and Coulton, arXiv:2609.04133v1, Section 2.1](https://arxiv.org/html/2609.04133v1#S2.SS1): it defines the moving-lens term through coherent potential translation and explicitly separates internal motions from that modeled term. This source was absent from the candidate.

Concrete independent analytic falsifier, with no numerical execution: in a periodic local Newtonian patch, freeze the background Poisson factor kappa > 0 and use conformal-time continuity
\[
 \nabla^2\phi=\kappa\delta,\qquad
 \delta'=-\nabla\cdot[(1+\delta)\mathbf v].
\]
Take
\[
 \phi=\epsilon\cos(kx),\qquad
 \mathbf v=V\sin(qy)\mathbf e_x,\qquad k,q>0.
\]
Choose epsilon and V small enough for positive total density and weak-field, slow-motion validity. The velocity is divergence-free and has curl
\[
 \nabla\times\mathbf v=-Vq\cos(qy)\mathbf e_z.
\]
The velocity-induced potential derivative required by Poisson plus continuity is
\[
 \phi'_{\rm vel}=
 \frac{\epsilon V k^3}{k^2+q^2}\sin(kx)\sin(qy),
\]
whereas pointwise potential advection would give
\[
 -\mathbf v\cdot\nabla\phi=
 \epsilon V k\sin(kx)\sin(qy).
\]
For q=k the first is half the second. This is an instantaneous consistency counterexample to the unrestricted extension, not a cosmological solution or a new moving-lens measurement. The two approach one another in the slow-velocity-variation limit q/k -> 0, as expected.

Minimal acceptable wording:

> The displayed response is the Jacobian of a prescribed potential-advection model. Its physical moving-lens interpretation applies to coherent translation, or to a declared scale-separated approximation in which the velocity varies slowly across the potential structure. A complete finite E/B basis does not establish this validity for arbitrary modes or amplitudes. For general matter-velocity perturbations the potential must be obtained from a qualified matter/dynamical response, including the relevant nonlocal and intrinsic-evolution terms.

Retain all signed E/B coefficients as formal bookkeeping; do not delete B to force consistency. Change the “True temperature response” heading to identify this conditional model. Label the local rotation example as an internal-motion/static-scalar-potential null, outside the rigid-bulk-motion observable; it cannot establish a rigid moving-halo or Bianchi no-go. The no-universal-B-blindness statement can remain, with this domain stated.

### F2 — P2: fixed template alone does not freeze fitted-amplitude weights

Location: candidate line 73.

The bandpower response LR is linear at fixed observed X and fixed linear processing. But the amplitude expression w^T LR is conditional on fixed covariance C and template t. The paper's Eq. 23 estimates covariance from the measured multipole products; Eqs. 24–25 then use that covariance in the fitted amplitude. Merely fixing X does not freeze w. [Hotinli et al., arXiv:2605.18938v1, Section III.3](https://arxiv.org/html/2605.18938v1#S3.SS3).

For b=w^T d and d=L R u, the general first variation is
\[
 \delta b=w^T L R\,\delta u+(\delta w)^T d.
\]
If t is fixed and only C changes, setting F=t^T C^{-1}t gives
\[
 \delta b=
 w^T\delta d-
 \frac{t^T C^{-1}(\delta C)C^{-1}(d-bt)}{F}.
\]
Variation of t contributes further terms. The scalar derivative still has rank at most one where differentiable, but its row need not equal w^T LR.

Minimal acceptable wording:

> With X and the bandpower processing held fixed, the bandpowers have response LR. With C and t also frozen, the fitted-amplitude response is w^T LR. If covariance or template are re-estimated, their derivative terms must be included; no evaluated full-pipeline Jacobian is available here.

No source estimator defect is inferred. The candidate's ker(LR) statement remains a conditional statement about the retained fixed-processing bandpowers, not the whole re-estimated likelihood.

## Source audit and checks that passed

| Source actually inspected | Evidence and conclusion |
|---|---|
| [Hotinli et al. 2605.18938v1](https://arxiv.org/html/2605.18938v1), cached HTML SHA256 de9b8aabb3f7a4f8f57a37987710bb58712486c3ce23f4f5f498025855af0331; Sections II, III.1–3, IV.1–2, V.3 | Density reconstruction, weighted template, TG/TC compression and normalization are distinct. The calibration caveat is supported. The reported amplitude is not beta or a released signed matter field. |
| [Author page](https://selimhotinli.github.io/movinglenseffect/), live Resources section and cached HTML | Paper and media links were observed; no numerical ACT–DESI measurement/covariance bundle was identified there. |
| [moving_lens tree 9e343c82930f0d8e4366507b5f1759f0559c8f09](https://github.com/selimhotinli/moving_lens/tree/9e343c82930f0d8e4366507b5f1759f0559c8f09) | Independent GitHub API retrieval: one entry, truncated=false, README blob e433b622c360d2e7d0d3db4b3c9a60a61a2732be. README defers code/data; releases API returned an empty list. This is a bounded repository observation. |
| [kszx tree c64f3fda498b25cc978b2a67909f3c8f916578fd](https://github.com/kmsmith137/kszx/tree/c64f3fda498b25cc978b2a67909f3c8f916578fd) and cached mlhack.py | Independent API tree has 99 entries, truncated=false. mlhack.py blob ed04d573d3e3168b6af03bc258c2dec79c6a7e34 produces a longitudinal vector from a scalar Fourier field and interpolates spherical components. A framework/helper is not this observation's calibrated data release. No upstream code was executed. |
| [kszx_notebooks tree 9dcce8cb4ce1f1e37074343444f0eae09d2bd046](https://github.com/kmsmith137/kszx_notebooks/tree/9dcce8cb4ce1f1e37074343444f0eae09d2bd046) | Independent API tree has 17 entries, truncated=false. Surrogate notebook blob 5edf87b897667509a7e33560dc47646522b89964 is present. Tree inspection supplies no final measurement/covariance bundle identity; notebook contents were not independently executed or fully audited. |
| [ACT NILC product listing](https://lambda.gsfc.nasa.gov/product/act/act_dr6.02/act_dr6.02_nilc_prod_table.html) and [PSPIPE listing](https://lambda.gsfc.nasa.gov/product/act/act_dr6.02/act_dr6.02_pspipe_prod_table.html) | Live official pages establish public map and cosmology-spectrum products. They do not identify covariance for the ACT–DESI TG/TC statistic. |
| [DESI LRG v1 catalogues](https://data.desi.lbl.gov/public/papers/c3/lrg_xcorr_2023/v1/catalogs/) | Cached listing and independent direct HTTP 200 agree: 1323-byte listing SHA256 ccf686082e9edc0cb13b0df05a1364387e3d69a784cba5ae13a0b1b0d4235925. Main/extended FITS sizes are 545264640 / 1484357760 bytes. No catalogue was downloaded. |
| [Wittman et al. 2609.38457v1, Section III.1](https://arxiv.org/html/2609.38457v1#S3.SS1) and [Zhang et al. 2610.04865v1](https://arxiv.org/html/2610.04865v1) | The first studies real spectra with inadequate precision for this signal; the second is a photon-noise forecast. Neither inspected paper supplies the required common cosmological transverse-field product. |
| [Wayland et al. 2609.04133v1](https://arxiv.org/html/2609.04133v1), Section 2.1 and opening operator definitions | New relevant theory evidence narrows the operator domain. Its galaxy-momentum scalar-cross-correlation selection statements do not establish arbitrary physical matter-curl blindness. No measurement bundle was obtained from this inspection. No broader code search or theory implementation was undertaken. |

The candidate correctly avoids three invalid promotions:

- curl(rho vhat)=grad rho cross vhat can be nonzero despite curl(vhat)=0; angular template B/C is not independent three-dimensional matter vorticity.
- A zero conditional cross-mean from an independent mean-zero velocity field does not fix the joint law. Its variance can change; a map null or full statistical degeneracy does not follow.
- The local lensing-gradient ambiguity assumes an unconstrained nuisance. External gradient information can break it; it is not a universal observational no-go.

The tangent count 2 N_r L(L+2) is correct for the stated real E/B basis. The thin-lens alpha and beta conventions are dimensionally consistent. Single-epoch velocities do not alone supply four-acceleration. These points remain conditional and supply no full (x,F,Pi,Q,G_F) state or new null law.

The existing 20261018 report and the checked published passages, REPORT_20261024_REV1/sections/08_result_scope.tex:64 and figures/atlas.tex:492, already limit their result to source-amplitude compression and an unbounded physical amplitude under missing error bounds. No repair of those passages or old numerical rerun is warranted by this review.

## Executable decision

The controller may request one text-only revision addressing F1 and F2, preserving the original candidate and its hash, followed by one targeted identity-bound closeout by this reviewer. This review does not authorize a map/catalogue fit, an old scalar-contrast rerun, a new allocation, or numerical implementation.

For original K03, retain HOLD_SOURCE_SPECIFIC_PHYSICAL_RESPONSE. The missing input is a source-qualified physical response for the retained signed modes and its matching covariance/calibration/nuisance specification. A numerical TG/TC release would help consumption of this study, but would not by itself supply the omega/A/beta Jacobian. Public raw maps alone do not define the missing experiment. Cross-covariance is needed for quantities actually combined; no independence is invented.

A distinct qualified raw-map experiment remains a possible future branch. Continue other independently READY branches now. H04 remains held and K04 retains its H04 dependency. No original acceptance, frozen 17/42 or alternate 18 count, R9 UNKNOWN state, one-use cost, scientific admission, native-transfer claim or publication state is promoted.

Execution boundary: existing checkout branch research/htt-adaptive-methods-20261023, HEAD d93605e66adfececa89b90681124b232a5f90220, origin https://github.com/cosmosapjw-quantum/htt_base.git. Existing dirty files were preserved. Reviewer output is confined to /mnt/extdrive/workdir/htt_open_data/r29_moving_lens_source_independent_review/. No repository mutation, child agent, clone, worktree, numerical campaign, ODE, native Boltzmann or CAS certificate occurred. GitHub web-tool failures and a guessed nonexistent 1812.03167v3 endpoint were resolved using GitHub APIs and the actual arXiv v1 record; they are not evidence of absent scientific data.

Signed: /root/r29_moving_lens_source_independent_review; independent source/theory scope only; observed runtime UNKNOWN.

