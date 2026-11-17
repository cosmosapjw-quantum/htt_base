# HTT literature and morphology delta, 2026-11-17

## 1. Scope and provenance

This is an independent comparison of the current retained HTT experiment with primary literature, plus one new read-only calculation on the existing data products. It is not a repetition of the repository-wide census and does not claim a new observation of shear, tilt or Bianchi geometry.

Read baseline: `research/r58-mixed-tensor-convergence-20261117`, commit `6fe19c5139004a1f281ec85c592e5ab4c7590d5f`. Internally read R58 `THEORY_LOOPS.md`, `MANUSCRIPT.md` (including the R59 result tables), `LITERATURE_REVIEW_KO.md`, and the native result/carrier metadata. The calculation reads `docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS/NATIVE_REPLAY/OWNED_TENSOR_RESULT.json`, SHA-256 `225e4ddd8c99552560ff8b54ad5b6c4ca5ffb52efbc5ff75d81ab2148a086711`.

The applied source workflow was mathbox literature-check. Discovery used Exa (15 requested search results over two search questions), SciSpace (one 12-result dipole search), Parallel (cosmography and Bianchi searches and targeted primary-text extraction), and independent web retrieval/search. Date horizon: 2026-11-17. This is a bounded English-language source comparison, not a global novelty proof. Primary versions are pinned below; extraction is not a byte-authenticated PDF cache. No complete external paper was copied into repository files.

## 2. Main assessment

R58/R59 already contains a coherent 32-row, 11-coefficient joint polar/STF likelihood with full cross-window and cross-block covariance, and explicitly states equality with GLS and score compression. It therefore should be assessed as an empirical methods/application result. The five-view names are not five independent observations, and the representation alone does not establish extra Fisher information or a new physical theory.

The closest competition is now unusually direct: covariant local cosmography has been fitted to CF4 and Pantheon+; full STF/multipole-vector reconstruction and cross-multipole covariance have also been used on CF4. A paper claiming novelty from tensorization, generic H(z,n), generic boost separation or mask-coupled covariance would overlap known work. A more defensible contribution is the effect of the exact source-window covariance and calibration freedom on specified physical functionals, with matched-data comparisons and explicit limits of the physical pullback.

The current covariance ablation remains an internal synthetic ablation. Vicente et al. already use a joint multipole covariance, so they must not be represented as assuming independent dipole and quadrupole blocks.

## 3. Verified primary-source comparison

| Source and exact primary version | Result actually checked | Relation to HTT and remaining bridge |
|---|---|---|
| [Heinesen 2021, arXiv:2010.06534v2](https://arxiv.org/html/2010.06534v2), especially Sections 2–5 | General-spacetime distance-redshift series and finite physically interpretable multipole coefficients; sourceward direction convention, signature (-+++), c=1. The leading directional rate contains expansion, acceleration dipole and shear quadrupole. | Known after translation of notation. Restoring c gives H_dir=Theta/3-A.n/c+sigma:nn. Finite-z inference requires higher derivatives/evolution and cannot identify every component from this local slope. |
| [Maartens et al. 2024, arXiv:2312.09875v3](https://arxiv.org/html/2312.09875v3), Eqs. 19–32 and Section 4 | Covariant boost transformations of energy, redshift, direction and the physical Hubble parameter. Geodesic dust has a matter-frame monopole and quadrupole. Using the uncorrected luminosity-distance slope in a moving frame can generate incorrect multipoles. | Known after translation. Keep observational boosts distinct from the chosen matter congruence, and transform distances and directions consistently with redshift. General acceleration in HTT goes beyond the dust subcase but is already covered by Heinesen's general congruence. |
| [Kalbouneh, Marinoni & Maartens, arXiv:2401.12291v2](https://arxiv.org/abs/2401.12291v2) | Connects expansion-rate-fluctuation multipoles to covariant cosmographic parameters and studies the matter–CMB relative motion, tested in axisymmetric analytic models. | Partial/adjacent to the joint HTT experiment. Generic physical interpretation and motion estimation are prior work; HTT needs a clearly different identifiable functional or inference result. |
| [Kalbouneh et al., arXiv:2510.02510v2](https://arxiv.org/html/2510.02510v2), Sections 2, 4.2, 6 and Appendix A | Fits CF4 and Pantheon+ over 0.01<z<0.1. CF4 measurement correlations are set to zero because no catalogue covariance is supplied. A common axis is fitted jointly across multipoles and shells; full harmonic fits and the axial restriction are both considered. | Most direct cosmography comparator. Its binning, sample, monopole handling and response differ. Do not equate measurement-noise assumptions with every cosmic-null assumption. A common-data axial/full-STF comparison is feasible inside HTT; reproducing their numerical results needs their precise sample and likelihood. |
| [Vicente et al. 2026, arXiv:2607.07821v1](https://arxiv.org/html/2607.07821v1), Eqs. 13–18, 26–28 and Sections IV–V | CF4 at 0.01<z<0.05; full degrees of freedom for ell=1,2,3 via harmonic/STF and Maxwell vectors. Mask inversion and maximum likelihood are compared. Eq. 26 uses full ell m–ell' m' covariance estimated from 1000 simulations with inverse-covariance correction. Their full-vector alignment test finds no anomalous alignment despite nearby multipole maxima. | Known after translation for STF and mask-coupled inference. A maximum direction is not a Maxwell vector or a tensor eigenaxis. HTT's novel application must concern its different source operator, cross-depth law, calibration or physical functionals. Primary text retrieved with Exa/Parallel after generic open failed. |
| [Boubel et al. 2025, arXiv:2412.14607v2](https://arxiv.org/abs/2412.14607v2) | Tully–Fisher directional zero-point inference in CF4; compares an H0 dipole with an isotropic H0 plus bulk motion. | Partial/adjacent. HTT should compare constant fractional dipole and velocity response within the same retained sample rather than compare quoted significances from different samples. |
| [Stiskalek, Desmond & Lavaux, arXiv:2509.14997v2](https://arxiv.org/abs/2509.14997v2) | Joint distance-relation calibration and latent-distance forward modelling with reconstructed peculiar velocities. A fitted zero-point dipole can absorb radial flow features; allowing a radially varying external velocity changes the physical interpretation. | Direct warning against reading a constant-offset fit as expansion anisotropy. HTT can test a finite, declared velocity-evolution basis using existing windows, while preserving degeneracies and selection. This is a methodological comparison, not a contradiction of either dataset result. |
| [Salzano et al., arXiv:2512.02526v2](https://arxiv.org/abs/2512.02526v2) | Log-distance-modulus analysis, catalogue internal diagnostics and conservative depth cuts; lower-depth anisotropy decreases after peculiar-velocity correction. | Partial/adjacent. HTT's log response is not new; empirical sensitivity to the sample/flow model is scientifically relevant. |
| [Das, Wandelt & Souradeep 2015, arXiv:1509.07137v1](https://arxiv.org/abs/1509.07137v1); [SIToolBox 2019](https://academic.oup.com/mnras/article/489/4/5889/5569656) | Bayesian inference of anisotropic covariance through BipoSH, including physical Doppler parameters. SIToolBox extends joint inference to anisotropic noise and masking. | Known after translation for general covariance inference. A CMB tensor carrier needs an explicit mean/covariance transfer and matched-data comparison, not a claim that BipoSH discards anisotropy orientation. |
| [Ferreira & Quartin, arXiv:2011.08385v2](https://arxiv.org/abs/2011.08385v2) and [companion arXiv:2107.10846](https://arxiv.org/abs/2107.10846) | Separate Doppler, aberration and dipole contributions in Planck data, correcting intensity-to-temperature conversion artifacts and handling beam/noise/mask. | Existing observational boost/intrinsic-dipole baseline. HTT low-ell morphology alone is not an equivalent measurement. The project's Commander-only choice is retained; this comparison does not authorize using unavailable component simulations. |
| [Roldan, Notari & Quartin, arXiv:1603.02664v2](https://arxiv.org/abs/1603.02664v2) | Shows model-dependent degeneracies of dipolar gravitational-potential effects with Doppler and aberration signals; complete aberration degeneracy requires a tuned radial profile in the analysed model. | Partial/adjacent. Different beta labels are insufficient: declare endpoint frames, radial dynamics and additional responses. This source does not prove a universal impossibility of distinguishing boost and tilt. |
| [Yoo, Magi & Huterer, arXiv:2507.08931v2](https://arxiv.org/abs/2507.08931v2) | Different cosmic dipole observables measure source–observer relative velocities with distinct redshift-dependent contributions; aligned directions need not imply identical amplitudes. | Useful response check for the project's multi-probe residual. Counts, supernova distances and CMB cannot share an unqualified universal response coefficient. |
| [Saadeh et al., arXiv:1605.07178v2](https://arxiv.org/html/1605.07178v2), model and likelihood sections | Tests near-isotropic VII_h and limiting I,V,VII_0 models with temperature and polarization, all shear modes, assumed perfect-fluid dynamics and consistent relative fluid motion. | A physical-template benchmark, not a universal all-Bianchi exclusion. Local STF shape does not recover spatial Lie-algebra type. Their constraints should not be applied directly to the current apparent CF4 tensor. |
| [Pereira & Pitrou, arXiv:1909.13688v2](https://arxiv.org/pdf/1909.13688v2) | Explicit near-isotropic correspondence for I,V,VII_0,VII_h,IX with FLRW perturbations, including super-curvature modes for open classes. | Literature-supported route to constructing broader transfer functions. Arbitrary strongly anisotropic/tilted classes are outside this perturbative correspondence. |
| [Alsing & Wandelt, arXiv:1712.00012v2](https://arxiv.org/abs/1712.00012v2), Sections 2–3 | Score compression preserves local Fisher information under regularity conditions; Gaussian mean and covariance responses give linear and quadratic score terms. | The current fixed-C linear-mean carrier has exact sufficient-statistic structure by direct factorization. General score compression is locally Fisher-optimal, not globally sufficient for arbitrary likelihoods. |

## 4. New executed result: axisymmetric confidence-set witnesses

Write the fitted STF block as k in R^5 with marginal covariance S. The declared fixed-Gaussian experiment gives the simultaneous marginal set

    E_5 = {k : (k-khat)^T S^-1 (k-khat) <= chi2_5(0.95)}.

For any unit n, define u(n)=sqrt(3/2) STF(nn), in the orthonormal STF5 chart. The axial family is k=a u(n), with signed Frobenius amplitude a. Its best amplitude for fixed n is exactly

    a(n) = [u(n)^T S^-1 khat] / [u(n)^T S^-1 u(n)].

Evaluating the residual quadratic at any candidate n supplies an explicit feasible point. If that value is below the confidence threshold, intersection is demonstrated; proving a global optimizer minimum is unnecessary. Conversely, failure to find a witness would not establish disjointness.

The threshold is chi2_5(0.95)=11.070497693516. The independently coded explicit STF basis, 2048 deterministic Fibonacci directions and 12 BFGS starts gave:

| nuisance variant | observed invariant shape | candidate residual quadratic | signed candidate amplitude | inside 95% marginal set |
|---|---:|---:|---:|---|
| log | 0.073860 | 5.028793300 | -0.025865194 | yes |
| log_mono | -0.193654 | 4.117408668 | -0.029628997 | yes |
| log_mono_error | -0.157411 | 4.090650559 | -0.028605816 | yes |
| log_mono_galactic | -0.106367 | 1.091064492 | 0.024328306 | yes |
| log_mono_radial | -0.370807 | 2.720279088 | -0.028807551 | yes |
| log_split | -0.580637 | 1.349595324 | -0.026837762 | yes |
| log_survey | -0.476511 | 1.847555195 | -0.026978926 | yes |

The observed shape is sqrt(6) tr(K^3)/[tr(K^2)]^(3/2); axial tensors have shape +/-1. All seven best-fit tensors lie away from those endpoint shapes, yet all seven confidence sets contain explicit axial tensors. Consequently the current experiment does not require triaxial morphology at this confidence-set level.

This is generic axial compatibility, not an independent verification of Kalbouneh's axis direction, common-axis hypothesis or redshift evolution. It does not supply an axial-versus-triaxial p-value, and the R58 covariance and post hoc-family limitations remain.

A full 11-coordinate witness was also constructed by the exact profile lift

    alpha_w = alphahat + Cov(alpha,k) S^-1 (k_w-khat).

Its 11-dimensional likelihood distance equals the 5-dimensional marginal distance. The maximum observed discrepancy was 2.665e-15. This independently verifies the set projection at the numerical precision of the existing carrier. Matrix traces, Frobenius norms, axis norms, tensor eigenvalues and invariant shapes are serialized in the JSON.

Artifacts:

- `literature_delta_axisym.py`: standalone read-only calculation, no HTT package import needed.
- `literature_delta_axisym.json`: source hash, versions, complete component witnesses and checks.
- Actual execution: one-thread Python on the authorized device; JSON output printed and copied to scratch only. No production file was changed.
- An initial package import failed because the ambient Python path did not expose `obsstat`; the final script removes that unnecessary package-import dependency and explicitly defines the already-declared STF basis.

## 5. Concrete next use of five-view methodology

The current unrestricted calibration quotient correctly says that individual shear/acceleration are unbounded. To make this scientifically informative without inventing a calibration prior, report a calibration-sensitivity function.

For k=s+q_cal and a declared sensitivity body q_cal in tau B_cal, the shear set is

    C_s(tau) = C_k + (-tau B_cal),
    h_Cs(v) = h_Ck(v) + tau h_Bcal(-v).

The smallest calibration scale that makes zero shear compatible is

    tau_star = min_{k in C_k} gauge_Bcal(k).

This is precisely the existing Q_min construction, now tied to an observable interpretation. With a Frobenius unit ball it reports the minimum STF calibration anisotropy needed to absorb the apparent tensor. A directional version uses F_support. It is a sensitivity threshold to be measured from the present carrier, not an asserted physical calibration bound. No finite tau should be adopted as a physical premise without an external justification.

Likewise, G_F should be used for a declared low-dimensional evolution hypothesis in the same full covariance, not just as a relabeling of a constant coefficient. Finite radial velocity bases address the actual issue raised by Stiskalek et al. A comparison between common-axis, unconstrained STF and fixed source-bound Bianchi templates should use one data law, preserving differences in rank and singular boundaries.

The novelty labels are therefore:

- Tensor/STF representation and Gaussian carrier: known after translation of notation.
- Generic boost/cosmography and template Bianchi inference: established source methods.
- Current cross-block-ablation covariance effect: project-specific numerical application; no literature-wide superiority claim.
- New axial witness calculation: project-specific observed compatibility result, derived and numerically checked.
- Calibration sensitivity via Q_min: constructive next application of an existing mathematical relation; actual threshold computation remains to be integrated by the root agent.
