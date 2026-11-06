# Local coding-agent resume prompt: HTT R39 tensor-x observational convergence

## Mission and immutable boundaries

Continue from the latest origin branch head of:
https://github.com/cosmosapjw-quantum/htt_base
Branch: research/r39-observational-identifiability-20261107
R38 parent: research/observational-convergence-r38-20261107 @ 05e9d53449bd02973848da3306f72f63edd7fc54

Do not merge main. Do not use Remote Desktop. Use the user's existing local checkout and actual local data cache. The purpose is to convert the R39 tensor-x theory/operator contract into a reproducible observed-data analysis.

The primary state is field-valued or explicitly basis-truncated theta_K={sigma_AB, omega_A, A_A, beta_RM_A, beta_MO_A}, with congruence/frame/epoch/triad metadata; beta_RO is a derived closure view, not a third independent velocity vector. The primary x[s,alpha]=phi_alpha(Z_s) bundle contains direct kinematical components, normalized copies, mixed kinematic functionals and predicted observable carriers. The ultimate target is one source-conditioned multi-probe L(theta,psi,eta;D)=p(D|theta,psi,eta) for D={a_lm,z_i,n_hat_i,fluxes,distance moduli,proper motions,...}; derive x,Q,Pi,F,G_F from one joint posterior/compatibility object. x_C remains an optional scalar ablation only.

## Non-destructive startup

1. Inspect git status --porcelain=v2, branch, HEAD, remotes, staged/unstaged diffs and untracked files before any operation.
2. Preserve every dirty/untracked user file. Do not reset, clean, force checkout, rebase or overwrite.
3. Fetch origin. Verify the exact R39 branch and start from its latest remote HEAD. If local branch diverges, stop and report both SHAs; never force-align.
4. Read all files in OBSERVATIONAL_CONVERGENCE_R39_20261107.
5. Read R38 adapters/scripts/results and pinned METHOD_REBOOT_20261023/THEOREMS.md T1–T7, tensor_joint_r9/revision2/MODEL_TO_DATA.md and THEORY_EXTENSION.md.
6. Preserve R38 source/result files immutably. Corrected products receive new IDs and provenance.

## Work package A: implement direct kinematical theta and vector/tensor x

Read KINEMATICAL_LIKELIHOOD_MODEL.md and KINEMATICAL_FUNCTIONAL_REGISTRY.json first. Implement or extend the existing typed structures; do not build a scalar x_C wrapper.

The common latent state is Z=(theta_K,psi,eta,xi). The primary kinematical block at one point/epoch is

theta_K={sigma_AB, omega_A, A_A, beta_RM_A, beta_MO_A}.

- sigma_AB: five STF2 polar components, s^-1.
- omega_A: three axial-vector components obtained by dualizing the spatial vorticity two-form, s^-1.
- A_A: three polar acceleration components, m s^-2.
- beta_RM_A: radiation-matter relative velocity, dimensionless.
- beta_MO_A: matter-observer relative velocity, dimensionless.
- beta_RO_A: derived radiation-observer view; first-order beta_RO=beta_RM+beta_MO+O(beta^2), exact composition requires ordered tetrads/Wigner rotation.
- optional DeltaOmega_k adds a distinct scalar geometry block; it is not the anisotropic spatial Ricci tensor.

Every beta vector must carry both physical_frame_id and spatial_basis_id. The spatial FrameTransport is only an orthogonal triad-axis change inside the same physical frame. It is not a Lorentz boost. Mixed beta functionals and beta_RO first-order closure require the two velocities to have been represented in a common physical tetrad; otherwise preserve their direct values and return RELATIVISTIC_FRAME_BRIDGE_REQUIRED. Exact relative-frame composition requires ordered tetrads and Wigner-rotation handling.
The 17-dimensional pointwise core count is a representation count only. If theta is field-valued, declare its space/time basis, truncation, initial/boundary data and prior/regularization. Arbitrary kinematic tuples are not automatically Einstein-matter solutions; impose the relevant 1+3 Ricci identities, constraints, matter conservation and dynamics before GR/Bianchi attribution.

The x functional registry must include all three roles:
1. direct identity functionals of sigma, omega, A, beta_RM and beta_MO;
2. normalized direct copies sigma/H, omega/H and A/(cH);
3. mixed functionals such as sigma_AB beta_RM^A beta_RM^B/H (even scalar), beta_RM^A omega_A/H (pseudoscalar), sigma^A_B beta_RM^B/H (polar vector), beta_RM cross omega/H (polar vector), beta_MO dot A/(cH), and tr(sigma^3)/H^3;
4. predicted observer-space carriers: CMB T/E/B a_lm, BipoSH, selected source-count multipoles, Gaia VSH and directional-distance multipoles.

Do not conflate observed a_lm with predicted a_lm(theta). Observed maps/catalogue rows are fixed data with source identity; predicted carriers vary across posterior draws or identified-set witnesses. BipoSH computed from the same a_lm are derived summaries, not extra independent data. The current ObservableIrrepState is observer/data-space only and does not represent physical sigma, omega or A.

Every functional has a stable ID, input state identity, output rank/representation/parity, units, frame, congruence, epoch/window, basis, normalization, anchor, response/provider, perturbative order, sample semantics and availability status. Preserve unavailable, undefined, empty, unbounded, disconnected and numerically unresolved cases separately.

For O(3), sigma' = R sigma R^T, A'=R A, beta'=R beta, omega'=(det R)R omega. Test all proper and improper transformations. SO(3) orbit views retain chirality; O(3) reflection quotient is a separate declared output. Any flattening for storage/SVD must declare its orthonormal basis, metric, units, parity transform and inverse reconstruction.

## Mandatory reuse check before implementing new observables

Do not create a parallel local-boost, low-ell pole or observable-irrep implementation before inspecting these predecessor branches and files:
- PR #7 / PR-251: identifiability-aware low-ell pole kernel (typed antipodal axis, eigen-gap abstention).
- PR #13 / PR-252: correlated real-sky shell a_lm generator with full cross-shell covariance and no jitter.
- PR #419 / PMG-WU-001: canonical ObservableIrrepBlock and ObservableIrrepState.
- PR #442 / PMG-WU-010: full-sky local-observer Lorentz pullback, STF2-to-STF3 response and stored-real harmonic ell=2 to ell=1,3 oracle. Scope is local boost only.
- PR #443 / PMG-WU-011 design and PR #444 source-equivalent synthetic execution: processed cut-sky response design, beam/pixel/window and nuisance structure. They do not establish an observed Planck response.
- PR #449: observable tensors, typed kinematical MES and response-limited identification report.
- PR #533 and #540/#544/#545: selection-law, CF4 source-window and finite-boost/radial identifiability work.
- PR #552/#553 and #557/#559: Planck T/POL mask distinctions, same-sky covariance, beam adapter and local data recovery boundaries; PR #558 is the immediate R9 same-sky/beam/covariance predecessor between #557 and #559.

Read the exact branch/head and current file contents of each relevant predecessor before importing or extending code. Separate direct reuse, required transform, conditional reuse and unverified predecessor claims. The novelty target is only the integrated source-conditioned multi-probe operator, cross-probe dependence model and identifiable vector/tensor functional quotient. Do not re-implement a full-sky boost kernel or pole tensor under a new name.

## Work package B: reuse existing R9 code safely

Read and reuse:
- htt/src/common/r9_product.py: ProductIntake and SharedStateEmbedding;
- htt/src/common/tensor_functionals.py: fixed contraction-fibre support only;
- htt/src/common/depth_path.py: fixed feature paths and full ordered covariance blocks;
- pinned T7 simultaneous functional-image, anchor, support and Pi contracts.

Do not overstate current capability: fixed_contraction_support requires fixed q and is not a confidence certificate; missing cross-covariance blocks return unavailable; the cosmology-wide TensorFunctionalBundle/operator adapter is not yet implemented.

For uncertain STF anchor q, retain its joint inverse image with the physical state. Do not insert q_hat and drop its uncertainty. Preserve disconnected/chiral strata; support functions represent only convex-hull support.

## Work package C: exact frames and physical dimensions

1. Run the R39 velocity regression suite. The two-frame function uses the exact non-collinear standard-boost transformation and the stable coefficient identity (gamma-1)/beta^2 = gamma^2/(gamma+1). Verify collinear, non-collinear, small-beta, zero-velocity, inverse/axis convention and subluminal limits.
2. The physical three-frame map beta_RO, beta_RM, beta_MO still needs an ordered tetrad/boost composition. Existing beta_MO=beta_RO-beta_RM is first-order only. Include Wigner rotation when the convention requires it.
3. Repair directional_hubble_variation: a physical acceleration in m s^-2 enters Delta H/H through A/(cH). Do not subtract dimensional acceleration from a dimensionless response.

## Work package D: source identity and single-probe observation operators

Start with the user's actual data cache. Rehash all reported R38 inputs. Record release/version, source file SHA, row keys, frame, coordinate order, units, selection, mask, beam, bandpass, covariance row order and exact covariance identity.

Probe order:
1. Planck PR3/PR4: observed frequency/split T/E maps and matched FFP/noise/foreground simulations. The observed map supplies the data vector; simulations calibrate the same estimator/mask/beam covariance. PR3/PR4 are same-sky processing products, not independent skies.
2. Quaia/NVSS/RACS: source rows, random catalogues, completeness, flux/spectral/redshift distributions, masks, component grouping, overlap IDs, local clustering and overdispersion. Acquire RACS from its official release if absent.
3. Gaia DR3/CRF3: source-level proper motion and full covariance, redshift/magnitude/color, cross-match IDs, scanning-law and frame-systematics templates. Separate E1, B1, E2.
4. Pantheon+: exact full 1701-row table/covariance, selected row IDs and two-axis subsetting.
5. CF4: reconcile official Table2/3/4, group/galaxy hierarchy, calibration, method pooling and selected-operator membership.
6. DESI: distinguish isotropic BAO compression from full angular clustering; isotropic compression is not sky-axis evidence.

Each observed data likelihood must fail closed if any required source/covariance/selection/operator identity is missing. Synthetic fixtures must live in a separate mode and directory and cannot emit observed claims.

Build one joint likelihood, not a post-hoc product of independent probe posteriors:

p(D|theta,psi,eta)=integral dxi p(xi|theta,psi) p(D|xi,theta,psi,eta,W,S).

Here xi carries shared primordial/LSS/foreground/overlapping-source fields. Factor probe likelihoods only conditionally on the shared latent state or after an admitted joint cross-covariance/conditional-independence proof. Missing covariance blocks do not default to zero.

Required likelihood lanes:
- CMB: latent full-sky real nonredundant T/E/B harmonic vector; actual component/frequency/split/beam/pixel/mask/filter operator; anisotropic mean and full off-diagonal covariance; matched mean-field/null simulations.
- Counts: selection-normalized point-process intensity over n_hat,z,flux/colour; local structure, randoms, component grouping, overlap and overdispersion.
- SN/CF4: mu_th=5 log10[d_L(z,n;theta,psi)/10pc], full covariance, calibration and peculiar-velocity terms; local z->0 law is not a finite-z provider.
- Gaia: source proper-motion tangent vectors with full astrometric covariance, E1/B1/E2 VSH and scan/reference-frame systematics.

The local sourceward Hubble expansion is H_u(n)=vartheta/3 - A.n/c + sigma_ab n^a n^b, so d_L=cz/H_u(n)+O(z^2) only in its local optical domain. Vorticity is absent from this leading radial contraction; it requires a separately specified higher-order/other response. The observer-MO Doppler term is distinct from intrinsic congruence acceleration.



## Work package E: response rank and vector/tensor functional identification

For each probe derive the actual estimator/forward response J_p=∂O_p/∂Z. Construct the full covariance including cross-probe terms where known. Whiten on the positive covariance support, project shared and product-specific nuisance directions in the same metric, and compute the quotient singular spectrum.

For functional phi_alpha, test local identification using ker(J_eff) subset ker(D phi_alpha). For nonlinear targets, test whether phi_alpha is constant on each observation fibre. Otherwise retain the full image K_alpha(D)=phi_alpha(C(D)). Report functional-specific rank, null/weak directions, condition on the supported quotient and sensitivity to masks/cuts/nuisance bases. Prior regularization cannot create data rank. For Gaussian summaries with parameter-dependent covariance, the Fisher diagnostic includes both mean and covariance derivatives:
F_ij=(d_i m)^T C^-1(d_j m)+(1/2)Tr[C^-1(d_i C)C^-1(d_j C)]. For Poisson counts use the point-process score/Fisher, not the Gaussian mean-Jacobian alone. Assess functional-specific identification from the full likelihood score/Fisher tangent; ker(J_eff) subset ker(Dphi) is the local mean-response criterion where that reduction is justified.

Run preregistered x ablations on identical observations/mocks:
- scalar x_C only;
- typed vector/tensor x;
- O(3) quotient;
- SO(3) quotient retaining chirality;
- channel ablations for CMB T/E, counts, Gaia E/B and distance multipoles.

The tensor version succeeds only if calibrated out-of-sample prediction, functional identification or coverage improves at controlled false-positive rate. A larger state vector alone is not a result.

## Work package F: full five-variable HTT outputs

Construct the joint posterior or simultaneous confidence/identified region first. Then:
- x: sample × typed functional values and full set images;
- Q: matching anchor/gauge/margin uncertainty;
- F: directional support, sample pushforward and measure-defined occupancy kept distinct;
- Pi: strict exceedance surface under a named law; not generically a p-value;
- G_F: full-covariance tensor functional depth path preserving initial level and all cross-shell blocks.

The five outputs are not independent parameters or likelihood factors. Q must use a matching admitted anchor; missing acceleration/velocity anchors remain unavailable. Pi requires a named null/posterior/predictive law and is not the likelihood. F separates directional support, sample pushforward and measure-defined occupancy. G_F retains the full field/function covariance and common-depth level.

No independent marginal recombination. No zero filling. Unknown physical mass remains unknown. Separate posterior pushforwards from confidence-set images and null p-values.

## Work package G: Cobaya and paper gate

Cobaya orchestrates the already validated actual-data likelihoods; it is not a downloader or anisotropic Boltzmann solver. Require source-bound preflight. Save full chains, YAML, package versions, input hashes, row hashes, operator/nuisance version, sampler diagnostics, PPC, leave-one-probe-out predictions and full output hashes.

Model ladder:
- M0: isotropic background + observer boost + selection/calibration/foreground/local structure nuisance;
- M1: M0 + gauge-invariant residual radiation long-mode response;
- M2: M1 + redshift-evolving STF shear; include matter-radiation tilt only if independently identified;
- M3: Bianchi I with actual dynamics and family transfer. Other families require their own solvers/transfers.

Do not claim Bianchi family identification without family-specific transfer and multiple independent observable sectors. Require injection bias <0.25 posterior SD, nominal 68/95% coverage, preregistered false-positive control, stable functional quotient and leave-one-probe-out prediction.

## Required outputs

Push only source manifests, code, tests, compact result JSON, covariance/response diagnostics, updated DAG/claim ledger, paper report and handoff. Do not push raw catalogues/maps or large chains.

Every outcome must distinguish literature-supported, derived, numerically checked, implementation-verified, observed, conjectural, unresolved and blocked. Preserve failures and exact exceptions. Do not report tests/sampler PASS without command, environment, exit code and logs.
