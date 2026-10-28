# Author framing: processed Commander morphology companion

This is conditional editorial preparation for the existing P2 companion. It is not an MC100 result or an independent review. Requested author runtime: gpt-6-astra/xhigh; observed: UNKNOWN. The final source candidate, qualified scientific return, numerical slots and manuscript review are pending.

## Placement and novelty memo — not manuscript text

Use a standalone `pr4_morphology_supplement/main.tex` beside the existing `radiation_supplement`, reached through a new `README_PR4_MORPHOLOGY.md`. Link back to the qualified parent `repair_01/report/main.pdf`. Do not edit the old README, either parent manuscript, historical manifests, radiation supplement or proof sources. The physical connection is that a component-separated map has a processing-dependent observable law, whereas the parent paper studies a stipulated finite frequency-response space. This experiment cannot provide the missing physical foreground budget or calibrate that paper's finite compensation frontier.

The contribution is a reproducible comparison of one specified low-multipole polarization statistic with a specified released processing ensemble, including its mask response and finite-simulation uncertainty. No literature novelty for the statistic is asserted. The source contract records selection of Commander from product availability before its morphology outcome; the already-seen 30 GHz split diagnostic must not select the mask, statistic, multipoles, draws or stopping. Pilot outputs establish execution only. They supply no pilot significance, precision conclusion or final qualification.

Everything between the public-text markers below is proposed scientific prose. The result paragraph is deliberately incomplete. Its bracketed slots must be filled only from the complete qualified source; no build labelled publication-ready may contain a pending slot.

<!-- BEGIN PROPOSED PUBLIC TEXT -->

# Low-multipole polarization morphology in processed Commander maps

## Observable and processing

We compare a fixed polarization morphology statistic in the Planck PR4 Commander full-mission map with the corresponding released NPIPE/Commander simulations. This is an experiment on processed maps. The related finite-bandpass calculation uses the 24 real signed coordinates of E and B at multipoles 2 and 3. Here multipole 4 is additionally required by the statistic. The experiment supplies neither a new spectral-rank result nor a measured bound on foreground moments.

The observed polarization comes from the NSIDE = 2048 Q and U extension of `COM_CMB_IQU-commander_4096_R4.00_full.fits`; the higher-resolution temperature extension is unused. Simulations are the fixed 100 full-mission products `npipe6v20_commander_cmb_2048_mc_0300_005a.fits` through `..._0399_005a.fits`. Each simulation identifier contributes one parent-sky realization. Temporal splits and alternative products of the same sky do not add independent realizations.

We retain Galactic coordinates and the released COSMO polarization convention. Observed Q and U are in K_CMB; simulated values are converted from microkelvin to kelvin before analysis. The binary Lollipop mask retains 1273 of 3072 NSIDE = 16 pixels. Each NESTED parent value is copied to its 16384 NSIDE = 2048 children, and the same mask is applied to native-resolution Q and U. The masked maps are reordered to RING for spin-two analysis with lmax = mmax = 4:

\[
 \widetilde a^X_{\ell m}=\mathcal A^X_{\ell m}[M Q,M U],
 \qquad X\in\{E,B\},\quad \ell=2,3,4.
\]

The delivered resolution is described as nominally 5 arcmin. No additional smoothing, beam inversion, noise subtraction or scalar transfer correction is applied. These coefficients retain the released processing response and the extra mask response. The complete signed E and B coefficients, satisfying \(\widetilde a^X_{\ell,-m}=(-1)^m\overline{\widetilde a^X_{\ell m}}\), are retained with their source, unit and processing metadata.

## A fixed parity-odd contraction

For each nonzero E multipole define

\[
 v_{\ell m}=\frac{\widetilde a^E_{\ell m}}
 {\left(\sum_{r=-\ell}^{\ell}|\widetilde a^E_{\ell r}|^2\right)^{1/2}},
 \quad
 J_{234}=\operatorname{Im}\sum_{m+n+p=0}
 \begin{pmatrix}2&3&4\\m&n&p\end{pmatrix}
 v_{2m}v_{3n}v_{4p},\qquad T=|J_{234}|.
\]

The sum uses every allowed signed index, with no additional symmetrization factor. Reality of the field and the Wigner-symbol symmetry make the unprojected contraction purely imaginary: its conjugate is \((-1)^{2+3+4}\) times itself. Common proper rotations preserve the contraction; coefficient parity reverses J and preserves T. These algebraic properties concern the extracted coefficients. Rotating a sky through a fixed Galactic mask is a different operation.

T is dimensionless and uses one field, one multipole triple, one map product and one mask. There is no maximization over these choices. Powers \(\widetilde C_\ell^X=(2\ell+1)^{-1}\sum_m|\widetilde a^X_{\ell m}|^2\), in K_CMB squared, and quadrupole–octupole axis alignment are descriptive quantities. An undefined descriptive axis does not invalidate an otherwise valid J. This contraction is distinct from \(\chi=\det(v,Qv,Q^2v)\); the sharp bound for that determinant and ideal spherical reference laws are not used to calibrate T.

## Released-pipeline reference and finite-simulation precision

The released simulation construction uses independent CMB realizations with end-to-end processing, fixed foreground and instrumental settings, and Commander mixing matrices estimated from the observed data, with amplitudes fitted for each simulation. We use this as a plug-in processed-map working law. Fixing estimated mixing matrices does not establish the exact conditional distribution given their estimates or unconditional physical coverage. The data products and processing genealogy are documented by the NPIPE release and the Planck Legacy Archive.

For the complete prescribed ensemble, define

\[
 B=100,\qquad k=\sum_{b=1}^{100}{\bf1}\{T_b\ge T_{\rm obs}\},
 \qquad \widehat\theta=k/B,\qquad p_{\rm rank}=(1+k)/(B+1).
\]

Ties are included. The smallest rank value is 1/101. Interpreting this rank as a Monte Carlo significance reference additionally assumes exchangeability of the observed statistic and simulated statistics under the stipulated working model. No selection or early stopping uses intermediate tail counts.

For the working-law tail probability \(\theta=\Pr_{\rm work}(T_*\ge T_{\rm obs})\), we report the two-sided 95% Clopper–Pearson interval from k successes in B independent simulation draws. Its endpoints are 0 for k = 0 or \(F^{-1}_{\mathrm{Beta}(k,B-k+1)}(0.025)\) otherwise, and 1 for k = B or \(F^{-1}_{\mathrm{Beta}(k+1,B-k)}(0.975)\) otherwise. The interval uses B binomial trials, not B + 1 pseudo-observations. Its half-width must meet the specified 0.105 precision criterion. It measures finite-simulation uncertainty in this tail probability, without accounting for unrepresented foreground, calibration or model uncertainty.

## Results and interpretation

For all 100 prescribed realizations, the observed value is **[PENDING_FINAL_T_OBS]**, with **[PENDING_FINAL_K]** inclusive exceedances. The empirical tail fraction is **[PENDING_FINAL_K_OVER_B]**, and the plus-one rank is **[PENDING_FINAL_P_RANK]**. The 95% binomial interval is **[PENDING_FINAL_CP_LOW, PENDING_FINAL_CP_HIGH]**, with half-width **[PENDING_FINAL_CP_HALF_WIDTH]**. Figure 1 displays the complete simulation distribution and observed statistic. The accompanying numerical tables retain every simulation and its signed E/B coefficients.

Three unit-norm harmonic inputs, E(2,0), a real-field E(3,|m|=1) mode and a real-field B(4,|m|=2) mode, illustrate the native-resolution mask-and-analysis response in Figure 2. Their outputs retain every E/B component through multipole 4. They are three selected response columns; they do not reconstruct the full analysis operator or an upstream NPIPE transfer matrix. The qualified numerical supplement records linearity, masked-pixel, unit, reality, parity, rotation and retained-coefficient stability checks.

The comparison quantifies compatibility with this particular processed-map working law. It does not measure a physical foreground budget, infer radiation stress or matter shear from E, identify a Bianchi family, or establish unconditional false-positive control.

Figure 1. Empirical survival fraction of T for all 100 fixed processed Commander realizations, with the observed value marked. At the observed threshold the inclusive fraction is k/100; the separately reported rank is (1+k)/101. The interval in the result table describes simulation-tail uncertainty under the working law.

Figure 2. Three selected columns of the common mask-and-spin-analysis response, shown in the real signed E/B representation at multipoles 2, 3 and 4. Rows within each multipole are m = 0 followed by (sqrt(2) Re, -sqrt(2) Im) for positive m. Each input has unit harmonic norm. Positive-m inputs for the last two columns are 1/sqrt(2) and i/sqrt(2), respectively, with negative m fixed by reality. The display includes inter-multipole and E/B coupling where present; it is not a complete transfer matrix.

<!-- END PROPOSED PUBLIC TEXT -->

## Editorial references and pending insertion

Use the cached, source-bound NPIPE/ESA/PLA material recorded in the scientific contract. Cite Planck Collaboration, *Planck intermediate results. LVII. Joint Planck LFI and HFI data processing*, A&A 643, A42 (2020), arXiv:2007.04997, for the simulation construction; cite the ESA Simulation_data page and exact delivered product records for product roles. The nominal-resolution descriptor has the distinct source listed in that contract (arXiv:2502.07654v1, Section 2.1); its SEVEM ensemble must not be imported into this Commander comparison. The implementer must verify citation metadata against those retained sources before freezing the bibliography. Exact installed software versions and per-input hashes belong in the numerical supplement.

No final p-value, confidence interval, result figure, numerical mask-response conclusion or publication-ready PDF has been produced by this framing. Bind final source and review first, then populate the result paragraph, generate the two figures and tables from cached qualified outputs, build, and submit the exact manuscript candidate to fresh independent review.
